# UI/UX em Detalhes

## Filosofia de Design
A Intranet foi desenhada com um perfil corporativo, premium e focado na usabilidade de missionários, líderes e voluntários. A identidade visual afasta-se de sistemas "frios", adotando uma postura acolhedora porém extremamente profissional.

## Design System
- **Paleta de Cores**: 
  - Fundo principal: `slate-900` (um azul noite escuro profundo) promovendo o conforto visual constante (Dark Mode nativo).
  - Acentos: Variações de `blue-500` a `blue-700` para transmitir confiança e clareza.
  - Alertas Críticos: Vermelho carmesim para perigo (deleções) e amarelo âmbar para bloqueios e avisos de validade.
- **Tipografia**: Google Fonts **Inter**. Moderna, limpa, legível em todos os tamanhos (Mobile e Desktop).
- **Glassmorphism**: Painéis flutuantes, modais e sidebars utilizam fundos com transparência (`bg-white/5` ou `bg-gray-800/80`) com desfoque traseiro (`backdrop-blur-md`). Isso confere um visual tridimensional sofisticado que se integra magicamente ao papel de parede imersivo configurado pelo administrador.

## Usabilidade e Navegação
- **Progressive Web App (PWA)**: O sistema quebra a barreira do navegador e pode ser instalado no iOS/Android, comportando-se como um app nativo (fullscreen, icon launcher, splash screen).
- **Responsive-First**: Todas as tabelas, botões e painéis se adaptam a telas pequenas. O módulo de assinaturas (LGPD) e controle de presença ("Minhas Escalas") possuem botões extragrandes para fácil acionamento na rua.
- **Micro-Interações**: Efeitos suaves ao passar o mouse em linhas de tabelas (`hover:bg-white/10`), botões que escalam suavemente ao clique, e transições de entrada (fade-in) para modais.
- **Feedback Constante**: Toast notifications elegantes e alertas sonoros (`winsound`) garantem que o usuário saiba que sua ação foi registrada com sucesso (Ex: "E-mail de convocação enviado!").
