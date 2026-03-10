from notion_sync import adicionar_lead

resultado = adicionar_lead(
    empresa   = "Teste Empresa DELETAR",
    cidade    = "São Paulo - SP",
    whatsapp  = "(11) 99999-9999",
    segmento  = "Restaurante",
    observacoes = "Card de teste — pode deletar",
)

print("✅ Funcionou!" if resultado else "❌ Deu erro — veja a mensagem acima")