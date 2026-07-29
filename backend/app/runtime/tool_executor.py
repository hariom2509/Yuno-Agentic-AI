from app.tools.web_search_tool import search_web
from app.tools.calculator_tool import calculate
from app.tools.report_generator_tool import generate_report
from app.tools.file_reader_tool import read_file


class ToolExecutor:

    @staticmethod
    def execute(
        tool_name,
        payload,
        db=None
    ):

        if tool_name == "web_search":
            return search_web(payload)

        if tool_name == "calculator":
            return calculate(payload)

        if tool_name == "report_generator":
            return generate_report(payload)

        if tool_name == "file_reader":
            return read_file(payload)

        if db:
            from app.models.skill import Skill
            skill = db.query(Skill).filter(Skill.name == tool_name, Skill.active == True).first()
            if skill:
                try:
                    local_env = {"payload": payload, "result": None}
                    exec(skill.code, {}, local_env)
                    return str(local_env.get("result", "Skill executed with no return result."))
                except Exception as e:
                    return f"Error executing custom skill '{tool_name}': {str(e)}"

        return "Tool not found"