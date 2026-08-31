# 🎮 Connexion Discord au dashboard

Deux réglages à faire une seule fois (~5 min). Ensuite, tout le monde se
connecte au dashboard avec son compte Discord.

## Étape 1 — Application Discord

1. https://discord.com/developers/applications → ouvre ton application
   existante (« Oil Roxwood Logs ») ou crée-en une.
2. Menu **OAuth2** :
   - copie le **Client ID**
   - clique **Reset Secret** → copie le **Client Secret**
   - dans **Redirects**, ajoute exactement :
     `https://prwdtdmdkhzwfyivaepw.supabase.co/auth/v1/callback`
   - **Save Changes**

## Étape 2 — Supabase

1. Ton projet Supabase → **Authentication → Sign In / Providers** → **Discord** :
   - active le provider
   - colle le **Client ID** et le **Client Secret** → Save
2. **Authentication → URL Configuration** :
   - **Site URL** : `https://poulpizar01.github.io/Oil-Roxwood/admin.html`
   - **Redirect URLs** → ajoute : `https://poulpizar01.github.io/Oil-Roxwood/admin.html`

## Comment ça marche

- Bouton **« Se connecter avec Discord »** → autorisation Discord → retour
  automatique sur le dashboard, connecté.
- **Premier lancement** (aucun compte) : le premier connecté devient **Direction**.
- Pour autoriser quelqu'un : Paramètres → Comptes d'accès → créer un compte
  avec **son pseudo Discord exact** comme identifiant. À sa première connexion,
  le compte est lié à son ID Discord pour de bon (le pseudo peut ensuite changer).
- Un Discord non autorisé voit un message « pas encore d'accès » avec son
  pseudo à transmettre à la direction.
- La connexion **identifiant + mot de passe** reste disponible en secours
  (panne Discord, comptes techniques…).
