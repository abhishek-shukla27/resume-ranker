import os

structure={
    "resume-ranker":[
        "app.py",
        "requirements.txt",
        ".gitignore",
        "LICENSE",
        "resume_paser.py",
        "jd_parser.py",
        "matcher.py",
        "sample_resume.pdf",
        "sample_jd.pdf",
        "utils/text_cleaner.py"
    ]
}

def create_project():
    for root,files in structure.items():
        print(f"Creating project folder:{root}")
        os.makedirs(root,exist_ok=True)
        for file_path in files:
            full_path=os.path.join(root,file_path)
            dir_name=os.path.dirname(full_path)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name,exist_ok=True)
            with open(full_path,'w',encoding='utf-8') as f:
                f.write("")
            print(f"Created file:{full_path}")

if __name__=="__main__":
    create_project()