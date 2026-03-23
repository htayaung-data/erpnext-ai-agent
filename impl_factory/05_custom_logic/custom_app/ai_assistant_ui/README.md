### AI Assistant UI

Chat Panel for ERP

### Active Surface

- `qwen-chat` is the active governed enterprise assistant surface.
- Legacy OpenAI/manual runtime code has been removed.
- A minimal FAC bridge is retained under `qwen_chat` for `frappe_assistant_core` report execution.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app ai_assistant_ui
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/ai_assistant_ui
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
