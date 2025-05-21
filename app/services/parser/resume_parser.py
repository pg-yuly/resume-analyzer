import os
import PyPDF2
from bs4 import BeautifulSoup
import html2text
from fastapi import UploadFile, HTTPException
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    """简历解析类，支持多种格式的简历"""

    def __init__(self, upload_dir: str):
        """
        初始化简历解析器
        
        Args:
            upload_dir: 文件上传目录
        """
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        
    async def save_upload_file(self, upload_file: UploadFile) -> str:
        """
        保存上传的文件
        
        Args:
            upload_file: 上传的文件对象
            
        Returns:
            str: 保存的文件路径
        """
        file_path = os.path.join(self.upload_dir, upload_file.filename)
        
        try:
            with open(file_path, "wb") as buffer:
                content = await upload_file.read()
                buffer.write(content)
            return file_path
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise HTTPException(status_code=500, detail=f"保存文件失败: {e}")

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """
        解析简历文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 解析后的简历数据
        """
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                return self._parse_pdf(file_path)
            elif file_ext == '.html':
                return self._parse_html(file_path)
            elif file_ext == '.txt':
                return self._parse_txt(file_path)
            elif file_ext == '.docx':
                return self._parse_docx(file_path)
            else:
                raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_ext}")
        except Exception as e:
            logger.error(f"解析文件失败: {e}")
            raise HTTPException(status_code=500, detail=f"解析文件失败: {e}")

    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """解析PDF格式的简历"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
                    
            return {
                "content": text,
                "format": "pdf",
                "path": file_path
            }
        except Exception as e:
            logger.error(f"PDF解析错误: {e}")
            raise HTTPException(status_code=500, detail=f"PDF解析错误: {e}")

    def _parse_html(self, file_path: str) -> Dict[str, Any]:
        """解析HTML格式的简历"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除script和style元素
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text()
            
            # 处理文本，删除多余空白
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                "content": text,
                "format": "html",
                "path": file_path
            }
        except Exception as e:
            logger.error(f"HTML解析错误: {e}")
            raise HTTPException(status_code=500, detail=f"HTML解析错误: {e}")

    def _parse_txt(self, file_path: str) -> Dict[str, Any]:
        """解析纯文本格式的简历"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                
            return {
                "content": text,
                "format": "txt",
                "path": file_path
            }
        except Exception as e:
            logger.error(f"TXT解析错误: {e}")
            raise HTTPException(status_code=500, detail=f"TXT解析错误: {e}")

    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """解析DOCX格式的简历"""
        try:
            # 这里只是一个示例，实际使用时需要导入相关库，如python-docx
            # 这里简单演示，实际项目需要完善
            import docx
            doc = docx.Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            
            return {
                "content": text,
                "format": "docx",
                "path": file_path
            }
        except ImportError:
            logger.error("未安装python-docx库，无法解析DOCX文件")
            raise HTTPException(status_code=500, detail="未安装python-docx库，无法解析DOCX文件")
        except Exception as e:
            logger.error(f"DOCX解析错误: {e}")
            raise HTTPException(status_code=500, detail=f"DOCX解析错误: {e}")

# 创建默认解析器实例
from app.core.config import settings
default_parser = ResumeParser(settings.UPLOAD_DIR) 