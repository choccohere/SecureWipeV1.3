import sys
import argparse
import os

# Add src to path if running from root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def main():
    parser = argparse.ArgumentParser(description="SecureWipe - Industrialized Data Erasure Utility")
    parser.add_argument("--cli", action="store_true", help="Launch directly into Command Line mode")
    parser.add_argument("--gui", action="store_true", help="Launch directly into Graphical User Interface mode")
    args = parser.parse_args()

    # Determine mode: 
    # 1. If --cli or --gui is specified, use that.
    # 2. If nothing is specified, ask the user (to avoid accidental GUI launch in headless environments)
    
    mode = None
    if args.cli:
        mode = "cli"
    elif args.gui:
        mode = "gui"
    else:
        print("SecureWipe - Mode Selection")
        print("1. Graphical User Interface (GUI)")
        print("2. Command Line Interface (CLI)")
        try:
            choice = input("Select mode (1/2) [Default=1]: ").strip()
            if choice == "2":
                mode = "cli"
            else:
                mode = "gui"
        except EOFError: # For non-interactive environments
            mode = "cli"
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)

    if mode == "cli":
        from secure_wipe.cli.app import run_cli
        run_cli()
    else:
        try:
            from secure_wipe.gui.app import SecureWipeApp
            app = SecureWipeApp()
            if app.winfo_exists():
                app.mainloop()
        except Exception as e:
            print(f"Failed to start GUI: {e}")
            print("Falling back to CLI...")
            from secure_wipe.cli.app import run_cli
            run_cli()

if __name__ == "__main__":
    main()
