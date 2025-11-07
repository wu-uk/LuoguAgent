from pydantic import BaseModel, Field
from typing import Optional, List

class ProblemDetails(BaseModel):
    title: Optional[str] = Field(None, description="提取题目的完整标题, 例如 'P4137 [模板]可持久化线段树 2（区间 MEX）'")
    background: str = Field(..., description="提取题目背景，如果没有则返回 '无'")
    description: str = Field(..., description="提取完整的题目描述")
    input_format: str = Field(..., description="提取输入格式说明")
    output_format: str = Field(..., description="提取输出格式说明")
    examples: List[dict] = Field(..., description="提取所有的输入输出样例。每个样例是一个字典，包含 'input' 和 'output' 键")
    notes: str = Field(..., description="提取说明/提示部分。注意：必须保留所有的数学符号、上标和格式。如果没有则返回 '无'")

class SolutionDetails(BaseModel):
    solution_text: str = Field(..., description="提取完整的题解思路和文字说明 (必须保留所有 LaTeX 数学公式)")
    author: Optional[str] = Field(None, description="提取题解的作者用户名")
    code: Optional[str] = Field(None, description="提取该题解对应的完整代码块")
    code_language: Optional[str] = Field(None, description="提取代码块的编程语言 (例如 C++, Python)")

class ProblemAnalysis(BaseModel):
    """用于分析算法题目的数据结构"""
    detailed_solution: str = Field(..., description="一份详细的、步骤清晰的题解")
    sample_code: str = Field(..., description="一份格式良好、有注释的 C++ 参考代码")
    keywords: List[str] = Field(..., description="解决此问题所需的核心知识点列表, 例如 ['动态规划', '01背包']")

