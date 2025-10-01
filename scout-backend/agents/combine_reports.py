from strands import tool
import os
from agents.shared_storage import storage_lock, report_filepaths_storage

@tool
def combine_reports(filepaths: list, output_path: str = "reports/final_report.md") -> str:
    """
    Combines the contents of the given report files into a single Markdown file.
    Args:
        filepaths: List of file paths to combine.
        output_path: Path to save the combined report.
    Returns:
        Path to the combined report file.
    """
    combined_content = ""
    for path in filepaths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                combined_content += f"\n\n---\n\n" + f.read()
        else:
            combined_content += f"\n\n---\n\n# Missing file: {path}\n"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with storage_lock:
        with open(output_path, 'w', encoding='utf-8') as out:
            out.write(combined_content)
        if output_path not in report_filepaths_storage:
            report_filepaths_storage.append(output_path)
    return output_path
