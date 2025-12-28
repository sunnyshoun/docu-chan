from types import FunctionType

TOOL_DOCS: dict[str, FunctionType] = {}

def tool_doc_register(func: FunctionType):
    TOOL_DOCS[func.__name__] = func
    return func

@tool_doc_register
def read_file(file_path: str, n: int) -> str:
    """
    read the first n liens of the file.
    Args:
        file_path: path of the file.
        n: only read first n liens of the file. set n to -1 for read the whole file.
    """
    ...
    
@tool_doc_register
def report_summary(path: str, is_important: bool, summary: str) -> None:
    """
    Use this function to output the summary of the file.
    Args:
        path: file path
        is_important: determine the importance of this file in writing document of this project.
        summary: The summary of this file.
    """
    ...

@tool_doc_register
def get_image_description(image_path: str) -> str:
    """
    Use this function to get description of image.
    Args:
        image_path: path of the image.
    """
    ...
