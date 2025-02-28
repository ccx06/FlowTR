from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.logs import logger
from actions.program_write import SimpleWriteCode, SimpleRunCode


class ProgramAssistedSolver(Role):
    """  Assistant to generate a program-of-thought solutions to the query. """
    name: str = "TeleCoder"
    profile: str = "Program-aided Solver"
    goal: str = "to generate clear programming ideas and robust Python code for a specific problem"

    def __init__(self, llm_config, prompt_template, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleWriteCode(config=llm_config, PROMPT_TEMPLATE=prompt_template), SimpleRunCode])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        result = await todo.run(msg.content)
        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg)
        return msg
