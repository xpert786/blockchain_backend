import subprocess
from django.core.management.base import BaseCommand
from django.core.management import call_command
import sys
 
class Command(BaseCommand):
    help = 'Safe Deploy: Stash changes, Pull, Migrate, Restart'
 
    def run_shell_command(self, command, description):
        self.stdout.write(f"⏳ {description}...")
        try:
            # Command run karein aur output capture karein
            result = subprocess.run(
                command, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Done: {description}"))
            # Debugging ke liye output print karein (optional)
            # self.stdout.write(result.stdout)
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed: {description}"))
            self.stdout.write(self.style.ERROR(f"Error Log:\n{e.stderr}"))
            # Agar error aaye to script yahin rok dein
            sys.exit(1)
 
    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting Deployment Sequence...")
 
        # 1. GIT STASH (Local changes ko hata kar clean karein)
        # Ye zaroori hai taki git pull fail na ho
        self.run_shell_command(["git", "stash"], "Stashing local changes")
 
        # 2. GIT PULL
        self.run_shell_command(["git", "pull", "origin", "master", "--no-rebase"], "Pulling code from Git")
 
        # 3. MIGRATIONS
        # Hum subprocess use kar rahe hain taaki agar migrate fail ho to pata chale
        self.run_shell_command(["python", "manage.py", "makemigrations"], "Making Migrations")
        self.run_shell_command(["python", "manage.py", "migrate"], "Migrating Database")
 
        # 4. SYSTEM CHECK
        self.stdout.write("⚙️  Running System Check...")
        call_command('check')
 
        # 5. RESTART GUNICORN
        # Note: Ensure sudo permissions are set correctly
        self.run_shell_command(["sudo", "systemctl", "restart", "gunicorn_blockchain.service"], "Restarting Gunicorn")
 
        self.stdout.write(self.style.SUCCESS("✨✨ DEPLOYMENT COMPLETED SUCCESSFULLY ✨✨"))