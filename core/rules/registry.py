class RuleEngine:
    """
    Registry for business rules (Actions and Conditions).
    Actions perform tasks (e.g., Send Email).
    Conditions return booleans (e.g., Stock > 0).
    """
    _actions = {}
    _conditions = {}

    @classmethod
    def register_action(cls, name):
        """Decorator to register an action."""
        def wrapper(func):
            if name in cls._actions:
                raise ValueError(f"Action '{name}' is already registered.")
            cls._actions[name] = func
            return func
        return wrapper

    @classmethod
    def register_condition(cls, name):
        """Decorator to register a condition."""
        def wrapper(func):
            if name in cls._conditions:
                raise ValueError(f"Condition '{name}' is already registered.")
            cls._conditions[name] = func
            return func
        return wrapper

    @classmethod
    def execute_action(cls, name, context):
        """Execute a registered action with the given context."""
        action_func = cls._actions.get(name)
        if not action_func:
            raise ValueError(f"Action '{name}' not found in registry.")
        return action_func(context)

    @classmethod
    def evaluate_condition(cls, name, context):
        """Evaluate a registered condition with the given context."""
        condition_func = cls._conditions.get(name)
        if not condition_func:
            raise ValueError(f"Condition '{name}' not found in registry.")
        return condition_func(context)

    @classmethod
    def get_registered_actions(cls):
        return list(cls._actions.keys())

    @classmethod
    def get_registered_conditions(cls):
        return list(cls._conditions.keys())
