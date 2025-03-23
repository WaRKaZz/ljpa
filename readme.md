# LJPA

LJPA - LinkedIn Job Posting Applier
A Telegram bot designed to streamline the job search process by aggregating vacancy posts from linkedin and submitting applications via email.

## Prerequisites
- Latest version of Docker installed
- Docker Compose installed

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/warkazz/ljpa.git
    cd linkedin-bot
    ```
2. Preconfigure your Telegram bot:
    - Create a new bot using [@BotFather](https://t.me/BotFather) on Telegram.
    - Follow the instructions to get your **BOT_TOKEN**.
    - Get your **CHAT_ID** by sending a message to your bot and using an API request like this:
      ```bash
      curl https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
      ```
      Find your `chat_id` in the response.
3. Copy the example environment file and configure your environment variables:
    ```bash
    cp .env_example .env
    ```
    Edit the `.env` file using any text editor and provide the necessary values.

    ### Environment Variables
    - `LINKEDIN_EMAIL`: Your linkedin account email.
    - `LINKEDIN_PASSWORD`: Password for your linkedin account.
    - `BOT_TOKEN`: Telegram bot token from @BotFather.
    - `CHAT_ID`: Your Telegram chat ID for receiving messages.
    - `SMTP_EMAIL`: Your email address used for sending applications.
    - `SMTP_PASSWORD`: Password for the SMTP email account.
    - `SMTP_PORT`: Port for the SMTP server (e.g., `587` for Gmail).
    - `SMTP_SERVER`: SMTP server address (e.g., `smtp.gmail.com`).
    - `CV_FILE_NAME_PDF`: Name of your CV in PDF format.
    - `CV_FILE_NAME_TXT`: Name of your CV in TXT format.
    - `EMAIL_SIGNATURE`: Custom email signature to be added at the end of your applications.
    - `NOVNC_PORT`: Port used for NoVNC if applicable.
    - `GPT4FREE_HOST`: Hostname or URL for GPT-4 API access.
    - `LINKEDIN_SEARCH_URL`: linkedin search URL with your specific search parameters.
    - `VNC_PASSWORD`: Password for accessing the NoVNC interface.

4. Start the application:
    ```bash
    docker-compose up -d
    ```

# First-Time Login to Leakding
A manual login to Leakding may be required. If you see a log message indicating that manual login is needed, follow these steps:
1. Open your browser and navigate to:
    ```
    http://localhost:8080/vnc.html
    ```
2. You will be prompted to enter the VNC password.
3. Use the password set in the `.env` file under `VNC_PASSWORD`.
4. Log in to your Leakding account using your credentials.

After the first login, the bot will handle the rest automatically.

## Scheduling the Bot
You can schedule the bot to run at specific intervals using `cron` or any other task scheduling tool.

### Using Crontab
1. Open the crontab editor:
    ```bash
    crontab -e
    ```
2. Add the following line to run the bot once per day (adjust the time as needed):
    ```bash
    0 9 * * * cd /path/to/linkedin-bot && docker-compose up --build --force-recreate
    ```
    This example runs the bot every day at 9 AM.

### Alternative Methods
- You can also use `systemd` timers, Docker's built-in scheduling, or external tools like `Anacron` if preferred.
- Ensure the Docker service is running when using these methods.

## Troubleshooting
- Ensure that Docker and Docker Compose are properly installed.
- Verify your `.env` file is correctly configured.
- Check logs using:
    ```bash
    docker-compose logs -f
    ```

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Contributing
Feel free to submit issues or pull requests for enhancements.

