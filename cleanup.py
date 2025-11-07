import glob
import os

def clean_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Clean empty lines (remove whitespace but preserve the newline)
    cleaned = [line.rstrip() + '\n' if line.strip() == '' else line for line in lines]
    
    # Ensure exactly one newline at the end of file
    while cleaned and cleaned[-1].strip() == '':
        cleaned.pop()
    cleaned.append('\n')
    
    with open(file_path, 'w', newline='\n') as f:
        f.writelines(cleaned)

def main():
    python_files = glob.glob('backend/app/*.py')
    for file_path in python_files:
        clean_file(file_path)

if __name__ == '__main__':
    main()