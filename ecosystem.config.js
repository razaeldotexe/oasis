module.exports = {
    apps: [
        {
            name: "oasis-bot",
            script: "src/main.py",
            interpreter: ".venv/bin/python",
            cwd: "./",
            env: {
                NODE_ENV: "production",
            },
            restart_delay: 5000,
            max_restarts: 10,
            error_file: "logs/pm2-error.log",
            out_file: "logs/pm2-out.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss",
        }
    ]
};
