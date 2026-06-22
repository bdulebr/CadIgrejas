with open(".env", "a", encoding="utf-8") as f:
    f.write("\nOPENAI_API_KEY=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\n")
with open("requirements.txt", "a", encoding="utf-8") as f:
    f.write("\nopenai==1.61.1\n")
print("Key adicionada e requirements atualizado")
