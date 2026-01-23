# Plano de Implementação: Delete de Sessões no Admin

## Visão Geral
Adicionar funcionalidade para deletar sessões de chat pelo painel admin, com confirmação antes da ação.

## Requisitos

### Funcionais
- [x] Endpoint DELETE /admin/sessions/{session_id}
- [x] Botão de delete na lista de sessões
- [x] Diálogo de confirmação antes de deletar
- [x] Feedback visual após delete (toast/notificação)
- [x] Atualizar lista após delete

### Não Funcionais
- [x] Deletar tanto do Redis quanto da memória
- [x] Tratar erros graciosamente

## Abordagem Técnica

### Backend
1. Criar função `delete_session(session_id)` em `cache.py`
   - Tentar deletar de ambos os prefixos: `chat:session:` e `docs_chat:session:`
   - Usar `delete_cached()` existente

2. Criar endpoint em `admin.py`
   - `DELETE /admin/sessions/{session_id}`
   - Retornar sucesso/erro

### Frontend
1. Adicionar mutation em `useAdminData.ts`
   - `useDeleteSession()` com `useMutation`
   - Invalidar query de sessions após sucesso

2. Adicionar botão e confirmação em `Admin.tsx`
   - Ícone de lixeira na lista de sessões
   - AlertDialog do shadcn/ui para confirmação
   - Toast de feedback

## Arquivos a Modificar

| Arquivo | Ação | Mudança |
|---------|------|---------|
| `app/cache.py` | Editar | Adicionar `delete_session()` |
| `app/admin.py` | Editar | Adicionar endpoint DELETE |
| `src/hooks/useAdminData.ts` | Editar | Adicionar `useDeleteSession()` |
| `src/pages/Admin.tsx` | Editar | Botão delete + confirmação |

## Tarefas

1. **Backend: cache.py** - Função `delete_session(session_id)`
2. **Backend: admin.py** - Endpoint `DELETE /admin/sessions/{session_id}`
3. **Frontend: useAdminData.ts** - Hook `useDeleteSession()`
4. **Frontend: Admin.tsx** - Botão delete com AlertDialog

## Critérios de Sucesso
- [ ] Deletar sessão do tipo "chat" funciona
- [ ] Deletar sessão do tipo "docs" funciona
- [ ] Confirmação aparece antes de deletar
- [ ] Lista atualiza após delete
- [ ] Feedback visual (toast) após ação
