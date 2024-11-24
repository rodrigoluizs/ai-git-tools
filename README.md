[![Coverage Status](https://coveralls.io/repos/github/rodrigoluizs/ai-git-tools/badge.svg?branch=main)](https://coveralls.io/github/rodrigoluizs/ai-git-tools?branch=main)
# AI Git Tools

The `agt` command-line tool leverages the power of AI to streamline your Git workflow. By analyzing your code changes, it automates the creation of intelligent commit messages, branch names, and pull requests, saving you time and ensuring consistency.

## Features

- **Branch Naming**: Automatically generate branch names based on conventional commit guidelines.
- **Commit Messages**: Create consistent and meaningful commit messages powered by AI.
- **Pull Request Creation**: Generate and open GitHub pull requests directly from your terminal.
- **Multi-Service Support**: Currently supporting only GitHub, other service providers will come soon.

## How It Works

1. **Identify Changes**:
    - It analyzes the differences between the branch you are currently working on and the base branch.
    - It collects staged, unstaged, and untracked changes to generate a context for the operation.
    - \* The tool must be executed in the root folder of a valid Git repository.

2. **Generate AI-Powered Suggestions**:
    - Using the collected differences as context, the tool generates suggestions for:
        - Commit messages
        - Pull request titles
        - Pull request descriptions
        - Branch names
   - You can choose one of two methods:
       1. **Call OpenAI Directly**: The tool uses OpenAI's latest model to generate suggestions.
       2. **Copy Prompt to Clipboard**: The tool copies the generated prompt to your clipboard so you can use your own AI model of choice.

3. **Handle Uncommitted Changes**:
    - If there are no committed changes, the tool will stage and commit them into a new branch with the suggested name.

4. **Create Pull Request**:
    - The tool creates a pull request on the appropriate platform (e.g., GitHub) with the suggested title and description.

5. **User Interaction**:
    - You have the opportunity to review and edit all suggestions before the operations are executed, ensuring flexibility and accuracy.



### Get Started
Download the latest release for your platform from the [GitHub Releases page](https://github.com/rodrigoluizs/ai-git-tools/releases).

On Linux/MacOS, make the binary executable:
```bash
chmod +x agt
```

## Usage

Run the tool directly from the command line:
```bash
agt
```

### Help
To display help documentation:
```bash
agt --help
```

## Requirements

- Git installed and configured
- GitHub personal access token (if using with GitHub)

## Configuration

Set up your environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key.
- `GITHUB_TOKEN`: Your GitHub personal access token.

## Contributing

Contributions are welcome\! Feel free to open issues or submit pull requests.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- [OpenAI](https://openai.com) for their powerful APIs.