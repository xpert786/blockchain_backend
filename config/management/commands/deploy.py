import subprocess
from django.core.management.base import BaseCommand
from django.core.management import call_command
 
class Command(BaseCommand):
    help = 'Automates Git pull, Migrations, and Server Restart'
 
    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting Deployment...")
 
        try:
            # --- STEP 1: GIT PULL ---
            self.stdout.write("⬇️  Git Pulling origin master...")
            # 'check=True' ka matlab hai agar git pull fail hua to script yahin ruk jayegi
            subprocess.run(["git", "pull", "origin", "master", "--no-rebase"], check=True)
 
            # --- STEP 2: DJANGO TASKS ---
            self.stdout.write("⚙️  Running MakeMigrations...")
            call_command('makemigrations')
 
            self.stdout.write("📦 Running Migrate...")
            call_command('migrate')
 
            self.stdout.write("✅ Checking System...")
            call_command('check')
 
            # --- STEP 3: RESTART GUNICORN ---
            self.stdout.write("🔄 Restarting Gunicorn Service...")
            # Ye command sudo ke sath chalegi. 
            subprocess.run(["sudo", "systemctl", "restart", "gunicorn_blockchain.service"], check=True)
 
            self.stdout.write(self.style.SUCCESS("✅ All Done! Deployment Successful."))
 
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"❌ Error in command execution: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ An unexpected error occurred: {e}"))