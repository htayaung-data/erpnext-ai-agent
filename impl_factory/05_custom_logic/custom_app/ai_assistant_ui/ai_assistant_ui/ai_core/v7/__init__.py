from __future__ import annotations


def dispatch_report_qa(*args, **kwargs):
    from ai_assistant_ui.ai_core.v7.dispatcher import dispatch_report_qa as _dispatch_report_qa

    return _dispatch_report_qa(*args, **kwargs)


def is_report_qa_tool(*args, **kwargs):
    from ai_assistant_ui.ai_core.v7.dispatcher import is_report_qa_tool as _is_report_qa_tool

    return _is_report_qa_tool(*args, **kwargs)


def report_qa_start_v7(*args, **kwargs):
    from ai_assistant_ui.ai_core.v7.runtime import report_qa_start_v7 as _report_qa_start_v7

    return _report_qa_start_v7(*args, **kwargs)


def report_qa_continue_v7(*args, **kwargs):
    from ai_assistant_ui.ai_core.v7.runtime import report_qa_continue_v7 as _report_qa_continue_v7

    return _report_qa_continue_v7(*args, **kwargs)

__all__ = [
    "dispatch_report_qa",
    "is_report_qa_tool",
    "report_qa_start_v7",
    "report_qa_continue_v7",
]
