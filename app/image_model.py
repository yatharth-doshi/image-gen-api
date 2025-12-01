    # image_model.py
import os
import subprocess
from dotenv import load_dotenv
from uuid import uuid4



load_dotenv()

# -----------------------------
# Install dependencies (run once outside script)
# -----------------------------
# Move all pip installs to requirements.txt or install manually before running
# Example:
# pip install -r requirements.txt

# -----------------------------
# Hugging Face login
# -----------------------------
from huggingface_hub import login as hf_login
def login_hf(token: str):
    """
    Login to Hugging Face Hub
    """
    hf_login(token=token, add_to_git_credential=False)


# -----------------------------
# Run 3D generation
# -----------------------------
run_py_path = "stable-fast-3d/run.py"
def generate_3d(input_image_path: str, output_path: str ) -> str:
    """
    Takes an input image and generates 3D output using the stable-fast-3d model.
    
    Args:
        input_image_path: Path to input image (jpg/png)
        output_dir: Directory to save generated 3D files
    
    Returns:
        Path to generated 3D output folder
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Unique filename for output (so each generation is separate)
    
    os.makedirs(output_path, exist_ok=True)

    # Run your 3D generation script
    command = f"python {run_py_path} {input_image_path} --output {output_path}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"3D generation failed:\n{result.stderr}")
    
   
    
    if not os.path.isdir(output_path):
        raise FileNotFoundError(f"Expected output directory not found: {output_path}")

    

    # Return the full file path (like "app/temp_output/abc123.png")
    return os.path.relpath(output_path, "app")

# -----------------------------
# Example usage (for testing)
# -----------------------------
if __name__ == "__main__":
    # Load Hugging Face token from environment variable
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        raise ValueError("Set HF_TOKEN environment variable for Hugging Face login")
    
    login_hf(hf_token)  
    
    # Example input
    input_image = "images/image6.jpg"
    output_folder = generate_3d(input_image, "/")
    
    print(f"3D files saved in: {output_folder}")
