# Progresso do Projeto

## Resumo
Este projeto é um sistema de login com uma interface gráfica e funcionalidades de administração. O administrador pode registrar novos usuários e gerenciar o acesso ao sistema.

---

## Estrutura Atual
### Backend
- **Framework**: Flask
- **Banco de Dados**: SQLite
- **Rotas**:
  - `/`: Serve o arquivo `index.html`.
  - `/admin`: Serve o arquivo `admin.html`.
  - `/login`: Valida o login do usuário.
  - `/register`: Permite ao administrador registrar novos usuários.
  - `/img/<path:filename>`: Serve imagens da pasta `img`.
  - `/<path:filename>`: Serve outros arquivos estáticos.

### Frontend
- **index.html**: Tela de login.
- **admin.html**: Página de administração para registrar novos usuários.

---

## Próximos Passos
1. Garantir que os arquivos estáticos (imagens, scripts, etc.) sejam carregados corretamente.
2. Testar o fluxo completo:
   - Login com o usuário padrão (`x` / `22`).
   - Redirecionamento para a página de administração.
   - Registro de novos usuários.
3. Adicionar melhorias visuais ou funcionais, se necessário.

---

## Histórico de Alterações
### Última Alteração
- Revertidas mudanças relacionadas ao uso de `bcrypt` para evitar problemas.
- Restaurado o código para o estado funcional anterior.
- Configurado o Flask para servir arquivos estáticos corretamente.