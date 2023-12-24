# Flask 'Anonymous' Feedback System

A simple Flask web application for collecting anonymous feedback.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Features

- User authentication and authorization using Flask-Security.
- Anonymous feedback collection through a web form.
- Admin interface for managing feedback and sending invites to feedback.
- API endpoints for feedback submission, and more.
- Swagger documentation for API endpoints.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2. Create a virtual environment and install dependencies:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Set up environment variables:

    Create a `.env` file in the project root and define the following variables:

    ```env
    # .env
    MAIL_SERVER=your-mail-server
    MAIL_PORT=your-mail-port
    MAIL_USE_TLS=True  # Set to False if not using TLS
    MAIL_USE_SSL=False  # Set to True if using SSL
    MAIL_USERNAME=your-mail-username
    MAIL_PASSWORD=your-mail-password
    MAIL_DEFAULT_SENDER=your-default-sender-email
    SQLALCHEMY_DATABASE_URI=sqlite:///feedback.db
    SECRET_KEY=your-secret-key
    ```

4. Initialize the database:

    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

## Usage

1. Run the application:

    ```bash
    flask run
    ```

2. Access the application in your web browser at `http://localhost:5000`.

3. Access the Swagger documentation at `http://localhost:5000/apidocs`.

## API Endpoints

- `/api/feedback`: Submit anonymous feedback.

For more detailed API documentation, refer to the Swagger documentation.

## Contributing

If you would like to contribute or add/request a feature to this project, please do.

## License

This project is licensed under the [MIT License](LICENSE).
