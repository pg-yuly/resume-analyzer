from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import BaseOutputParser
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import logging
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeAnalysisResult(BaseModel):
    """简历分析结果模型"""
    matches_requirements: bool = Field(description="简历是否符合要求")
    match_score: float = Field(description="匹配度评分 (0-100)")
    reasoning: str = Field(description="分析原因的详细解释")
    skills_match: Dict[str, bool] = Field(description="每项技能的匹配情况")
    experience_match: bool = Field(description="工作经验是否符合要求")
    education_match: bool = Field(description="教育背景是否符合要求")
    strengths: List[str] = Field(description="候选人的优势")
    weaknesses: List[str] = Field(description="候选人的不足")
    summary: str = Field(description="总结评价")

class PydanticParser(BaseOutputParser):
    """输出解析器，将LLM输出解析为ResumeAnalysisResult对象"""
    
    def __init__(self):
        self.pydantic_parser = PydanticOutputParser(pydantic_object=ResumeAnalysisResult)
    
    def parse(self, text: str) -> ResumeAnalysisResult:
        try:
            # 尝试直接解析JSON格式
            if text.startswith("{") and text.endswith("}"):
                try:
                    json_obj = json.loads(text)
                    return ResumeAnalysisResult.parse_obj(json_obj)
                except json.JSONDecodeError:
                    pass
            
            # 回退到Pydantic解析器
            return self.pydantic_parser.parse(text)
        except Exception as e:
            logger.error(f"解析LLM输出失败: {e}")
            logger.error(f"原始文本: {text}")
            # 如果解析失败，创建一个默认结果
            return ResumeAnalysisResult(
                matches_requirements=False,
                match_score=0.0,
                reasoning="解析AI输出时出错",
                skills_match={},
                experience_match=False,
                education_match=False,
                strengths=[],
                weaknesses=["无法正确解析简历"],
                summary="解析错误，请重试"
            )

class ResumeAnalyzer:
    """简历分析器，使用AI评估简历是否符合要求"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4"):
        """
        初始化简历分析器
        
        Args:
            api_key: OpenAI API密钥
            model_name: 使用的模型名称
        """
        self.api_key = api_key
        self.model_name = model_name
        self.output_parser = PydanticParser()
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            openai_api_key=api_key,
            temperature=0.2,
            max_tokens=3000
        )
        
        # 创建提示模板
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
            你是一位专业的人力资源专家，擅长分析简历并匹配职位要求。
            你的任务是详细分析简历内容，并根据给定的职位要求评估候选人是否合适。
            请提供详细的分析和理由，而不是简单的是/否答案。
            
            你的分析应该包括：
            1. 技能匹配度：候选人是否具备所需的技术和软技能
            2. 工作经验：候选人的经验是否符合要求的年限和相关度
            3. 教育背景：候选人的学历是否符合要求
            4. 优势分析：候选人的突出优势
            5. 不足分析：候选人的潜在不足
            6. 总体匹配度评分和详细理由
            
            请以JSON格式返回分析结果，遵循以下结构：
            ```
            {
                "matches_requirements": bool, // 整体是否符合要求
                "match_score": float, // 匹配度评分(0-100)
                "reasoning": string, // 详细分析原因
                "skills_match": {}, // 各项技能的匹配情况
                "experience_match": bool, // 工作经验是否匹配
                "education_match": bool, // 教育背景是否匹配
                "strengths": [], // 候选人优势列表
                "weaknesses": [], // 候选人不足列表
                "summary": string // 总结评价
            }
            ```
            """),
            ("human", """
            ## 职位要求
            {requirements}
            
            ## 简历内容
            {resume_content}
            
            请分析这份简历是否符合上述职位要求，并提供详细分析。
            """)
        ])
        
    async def analyze_resume(self, resume_content: str, requirements: Dict[str, Any]) -> ResumeAnalysisResult:
        """
        分析简历是否符合要求
        
        Args:
            resume_content: 简历内容文本
            requirements: 职位要求信息
            
        Returns:
            ResumeAnalysisResult: 分析结果
        """
        
        # 将要求转换为结构化文本
        formatted_requirements = self._format_requirements(requirements)
        
        try:
            # 准备提示
            chain = self.prompt_template | self.llm
            
            # 发送到LLM
            response = await chain.ainvoke({
                "resume_content": resume_content,
                "requirements": formatted_requirements
            })
            
            # 解析结果
            analysis_result = self.output_parser.parse(response.content)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"简历分析过程中出错: {e}")
            # 返回默认失败结果
            return ResumeAnalysisResult(
                matches_requirements=False,
                match_score=0.0,
                reasoning=f"分析过程中出错: {str(e)}",
                skills_match={},
                experience_match=False,
                education_match=False,
                strengths=[],
                weaknesses=["分析过程出错"],
                summary="无法完成分析，请重试"
            )
            
    def _format_requirements(self, requirements: Dict[str, Any]) -> str:
        """将要求字典转换为格式化文本"""
        
        formatted = "职位要求：\n"
        
        if "job_title" in requirements:
            formatted += f"职位名称: {requirements['job_title']}\n\n"
            
        if "experience_years" in requirements:
            formatted += f"工作经验: {requirements['experience_years']}年以上\n\n"
            
        if "education" in requirements:
            formatted += f"教育背景: {requirements['education']}\n\n"
            
        if "skills" in requirements and requirements["skills"]:
            formatted += "技能要求:\n"
            for skill in requirements["skills"]:
                if isinstance(skill, dict) and "name" in skill and "level" in skill:
                    formatted += f"- {skill['name']}: {skill['level']}\n"
                else:
                    formatted += f"- {skill}\n"
            formatted += "\n"
            
        if "description" in requirements:
            formatted += f"职位描述:\n{requirements['description']}\n\n"
            
        return formatted

# 创建默认分析器实例
default_analyzer = ResumeAnalyzer(api_key=settings.OPENAI_API_KEY, model_name=settings.OPENAI_MODEL) 