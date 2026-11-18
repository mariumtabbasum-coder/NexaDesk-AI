import json, os
class JsonStore:
    def __init__(self,path,default):
        self.path=path; self.default=default
        os.makedirs(os.path.dirname(path),exist_ok=True)
        if not os.path.exists(path): self.write(default)
    def read(self):
        try:
            with open(self.path,"r",encoding="utf-8") as f: return json.load(f)
        except (json.JSONDecodeError,FileNotFoundError): return self.default
    def write(self,data):
        with open(self.path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
