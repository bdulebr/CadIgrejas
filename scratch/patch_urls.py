with open("core/urls.py", "r", encoding="utf-8") as f:
    content = f.read()

new_route = "    path('api/eversinho/chat/', views.eversinho_chat_api, name='eversinho_chat_api'),"

if new_route not in content:
    content = content.replace("    path('api/eversinho-status/<int:log_id>/', views.eversinho_status_api, name='eversinho_status_api'),",
                              "    path('api/eversinho-status/<int:log_id>/', views.eversinho_status_api, name='eversinho_status_api'),\n" + new_route)
    with open("core/urls.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("URL do Eversinho adicionada!")
else:
    print("URL já existe.")
