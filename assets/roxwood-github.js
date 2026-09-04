/* ============================================================
   OIL ROXWOOD — MOTEUR GITHUB
   Remplace Supabase. Aucun serveur : le dépôt EST la base.

   · identité      : Discord OAuth « implicite » (aucun secret)
   · lecture       : fichier public, sans jeton, sans limite
   · écriture      : API GitHub Contents avec un jeton personnel
   · concurrence   : le SHA du fichier fait office de jeton de version
   · « temps réel » : sondage régulier + au retour sur l'onglet

   Tout l'état partagé tient dans UN fichier : data/etat.json.
   Un seul fichier = un seul SHA = aucun conflit entre sections.
   ============================================================ */
(function (global) {
  "use strict";

  var CFG = global.ROXWOOD_CFG || {};
  var RAW = "https://raw.githubusercontent.com/" + CFG.owner + "/" + CFG.repo + "/" + CFG.branche + "/" + CFG.fichier;
  var API = "https://api.github.com/repos/" + CFG.owner + "/" + CFG.repo + "/contents/" + CFG.fichier;

  var CLE_JETON = "orx_ghtoken";
  var CLE_IDENT = "orx_discord";

  /* ---------- jeton d'écriture ---------- */
  function jeton() { try { return localStorage.getItem(CLE_JETON) || ""; } catch (e) { return ""; } }
  function poserJeton(t) {
    try { t ? localStorage.setItem(CLE_JETON, t.trim()) : localStorage.removeItem(CLE_JETON); } catch (e) {}
  }
  function peutEcrire() { return !!jeton(); }

  function enTetes(avecJeton) {
    var h = { "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
    if (avecJeton && jeton()) h["Authorization"] = "Bearer " + jeton();
    return h;
  }

  /* ---------- encodage UTF-8 ↔ base64 ---------- */
  function versB64(txt) {
    var o = new TextEncoder().encode(txt), s = "";
    for (var i = 0; i < o.length; i++) s += String.fromCharCode(o[i]);
    return btoa(s);
  }
  function depuisB64(b64) {
    var s = atob(b64.replace(/\s/g, "")), o = new Uint8Array(s.length);
    for (var i = 0; i < s.length; i++) o[i] = s.charCodeAt(i);
    return new TextDecoder().decode(o);
  }

  /* ---------- lecture ---------- */
  /* Sans jeton on passe par raw.githubusercontent : aucune limite de débit.
     Le CDN garde le fichier ~5 min, d'où le paramètre anti-cache.            */
  function lire() {
    return fetch(RAW + "?t=" + Date.now(), { cache: "no-store" })
      .then(function (r) {
        if (r.status === 404) return null;              // première installation
        if (!r.ok) throw new Error("lecture HTTP " + r.status);
        return r.json();
      });
  }

  /* Lecture authentifiée : donne aussi le SHA, indispensable pour écrire.

     Attention au 404 : sur cette adresse il veut dire DEUX choses très
     différentes — « le fichier n'existe pas encore » (première installation)
     ou « ton jeton n'a pas accès à ce dépôt ». GitHub répond volontairement
     la même chose dans les deux cas, pour ne pas révéler l'existence d'un
     dépôt à quelqu'un qui n'y a pas droit. On renvoie donc le drapeau
     `absent`, et c'est `verifierAcces()` qui tranche. */
  function lireAvecSha() {
    return fetch(API + "?ref=" + CFG.branche + "&t=" + Date.now(),
                 { headers: enTetes(true), cache: "no-store" })
      .then(function (r) {
        if (r.status === 404) return { data: null, sha: null, absent: true };
        if (!r.ok) return r.json().then(function (j) { throw new Error(j.message || "HTTP " + r.status); });
        return r.json().then(function (j) {
          var d = null;
          try { d = JSON.parse(depuisB64(j.content)); } catch (e) {}
          return { data: d, sha: j.sha };
        });
      });
  }

  /* ---------- le jeton peut-il vraiment écrire ICI ? ----------

     Lire n'est pas écrire. Le dépôt est public : n'importe quel jeton, même
     un jeton sans le moindre droit dessus, lit le fichier sans problème.
     Vérifier un jeton en lisant ne prouve donc rien — c'est exactement
     l'erreur qui a fait croire à un RH que son jeton marchait alors que
     chacune de ses saisies restait dans son navigateur.

     On interroge le dépôt lui-même : GitHub y répond `permissions.push`,
     qui est la seule réponse qui compte.                                  */
  function verifierAcces() {
    if (!jeton()) return Promise.resolve({ ok: false, code: "aucun",
      msg: "Aucun jeton enregistré — le dashboard est en lecture seule." });
    return fetch("https://api.github.com/repos/" + CFG.owner + "/" + CFG.repo + "?t=" + Date.now(),
                 { headers: enTetes(true), cache: "no-store" })
      .then(function (r) {
        if (r.status === 401) return { ok: false, code: "invalide",
          msg: "Jeton refusé par GitHub : expiré, révoqué, ou mal recopié (un espace, un retour à la ligne)." };
        if (r.status === 403) return { ok: false, code: "interdit",
          msg: "GitHub refuse ce jeton sur ce dépôt. S'il est « fine-grained » et créé sur un autre compte que " + CFG.owner + ", il ne marchera jamais ici." };
        if (r.status === 404) return { ok: false, code: "invisible",
          msg: "Ce jeton ne voit pas le dépôt " + CFG.owner + "/" + CFG.repo + ". Deux causes : le compte n'est pas collaborateur du dépôt, ou c'est un jeton « fine-grained » — ceux-là ne donnent accès qu'aux dépôts du compte qui les a créés. Il faut un jeton CLASSIQUE avec la portée public_repo." };
        if (!r.ok) return { ok: false, code: "http" + r.status,
          msg: "GitHub a répondu HTTP " + r.status + "." };
        return r.json().then(function (j) {
          var perm = j.permissions || {};
          if (perm.push || perm.admin || perm.maintain)
            return { ok: true, code: "ok",
              msg: "Écriture autorisée sur " + CFG.owner + "/" + CFG.repo + "." };
          return { ok: false, code: "lecture",
            msg: "Ce jeton voit le dépôt mais n'a pas le droit d'y écrire. Il manque soit l'invitation en collaborateur avec le rôle Write, soit la permission « Contents : Read and write » sur le jeton." };
        });
      })
      .catch(function (e) {
        return { ok: false, code: "reseau",
          msg: "Impossible de joindre GitHub : " + (e && e.message || e) };
      });
  }

  /* ---------- écriture ---------- */
  function ecrire(objet, sha, message) {
    var corps = {
      message: message || "MAJ dashboard",
      content: versB64(JSON.stringify(objet, null, 1)),
      branch: CFG.branche
    };
    if (sha) corps.sha = sha;
    return fetch(API, { method: "PUT", headers: enTetes(true), body: JSON.stringify(corps) })
      .then(function (r) {
        if (r.status === 409 || r.status === 422) return { conflit: true };   // quelqu'un a écrit avant nous
        if (!r.ok) return r.json().then(function (j) { throw new Error(j.message || "HTTP " + r.status); });
        return r.json().then(function (j) { return { sha: j.content && j.content.sha }; });
      });
  }

  /* ---------- fichiers joints (photos de factures, captures) ----------
     Une photo pèse 60 à 80 Ko. Rangée en base64 dans data/etat.json, elle
     serait relue par chaque navigateur ouvert toutes les 45 secondes et
     renvoyée en entier à chaque enregistrement. Elle devient donc un vrai
     fichier du dépôt, et l'état ne garde que son chemin — que les balises
     <img src="..."> acceptent tel quel.

     Chaque fichier a son propre SHA, donc son envoi n'entre jamais en
     concurrence avec l'écriture de l'état.                                */
  var API_BASE = "https://api.github.com/repos/" + CFG.owner + "/" + CFG.repo + "/contents/";

  /* dataURI -> { chemin } si l'envoi passe, { erreur } sinon. */
  function televerser(chemin, dataURI, message) {
    var m = /^data:([^;]+);base64,(.*)$/.exec(String(dataURI || ""));
    if (!m) return Promise.resolve({ erreur: "ce n'est pas une image encodée" });
    if (!jeton()) return Promise.resolve({ erreur: "aucun jeton d'écriture" });
    var corps = { message: message || "Ajout d'une pièce jointe", content: m[2], branch: CFG.branche };
    return fetch(API_BASE + chemin, { method: "PUT", headers: enTetes(true), body: JSON.stringify(corps) })
      .then(function (r) {
        if (r.ok) return { chemin: chemin };
        return r.json().then(function (j) { return { erreur: j.message || "HTTP " + r.status }; },
                             function () { return { erreur: "HTTP " + r.status }; });
      })
      .catch(function (e) { return { erreur: String(e.message || e) }; });
  }

  /* Suppression au mieux : un fichier orphelin ne casse rien, une erreur
     bloquante en pleine suppression de facture, si.                        */
  function supprimerFichier(chemin, message) {
    if (!jeton() || !chemin || chemin.indexOf("data:") === 0) return Promise.resolve(false);
    return fetch(API_BASE + chemin + "?ref=" + CFG.branche, { headers: enTetes(true), cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.sha) return false;
        return fetch(API_BASE + chemin, {
          method: "DELETE", headers: enTetes(true),
          body: JSON.stringify({ message: message || "Retrait d'une pièce jointe", sha: j.sha, branch: CFG.branche })
        }).then(function (r) { return r.ok; });
      })
      .catch(function () { return false; });
  }

  /* ============================================================
     IDENTITÉ DISCORD — flux implicite, aucun secret côté client
     ============================================================ */
  function urlRetour() { return location.origin + location.pathname; }

  /* Identifiant du serveur Discord. Ce n'est pas un secret (tout le monde sur le
     serveur peut le lire), mais il est réglable depuis Paramètres plutôt que codé
     en dur. Tant qu'il est vide, on ne demande QUE `identify` : la lecture des
     rôles n'est réclamée à l'utilisateur que si elle sert vraiment à quelque chose. */
  var SERVEUR = CFG.discordGuild || "";
  function configurerServeur(id) { SERVEUR = String(id || "").trim(); }
  function serveur() { return SERVEUR; }

  function connexionDiscord() {
    if (!CFG.discordClientId) {
      alert("Connexion Discord non configurée : renseigne discordClientId dans admin.html.");
      return;
    }
    var scope = SERVEUR ? "identify guilds.members.read" : "identify";
    var u = "https://discord.com/api/oauth2/authorize"
      + "?client_id=" + encodeURIComponent(CFG.discordClientId)
      + "&redirect_uri=" + encodeURIComponent(urlRetour())
      + "&response_type=token&scope=" + encodeURIComponent(scope);
    location.href = u;
  }

  /* Au retour de Discord, le jeton arrive dans le fragment (#access_token=…).
     On s'en sert une seule fois pour lire l'identité, puis on l'oublie. */
  function recupererIdentite() {
    var h = location.hash || "";
    if (h.indexOf("access_token=") < 0) return Promise.resolve(identiteLocale());
    var p = new URLSearchParams(h.slice(1));
    var tok = p.get("access_token");
    history.replaceState(null, "", location.pathname + location.search);  // on nettoie l'URL
    if (!tok) return Promise.resolve(identiteLocale());
    return fetch("https://discord.com/api/users/@me", { headers: { Authorization: "Bearer " + tok } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (u) {
        if (!u) return identiteLocale();
        var id = {
          did: u.id,
          pseudo: u.global_name || u.username || "inconnu",
          avatar: u.avatar ? "https://cdn.discordapp.com/avatars/" + u.id + "/" + u.avatar + ".png" : ""
        };
        return rolesServeur(tok).then(function (m) {
          /* `roles` absent = on n'a pas pu savoir (serveur non réglé, permission
             refusée, personne pas sur le serveur). Un tableau vide veut dire
             « sur le serveur, mais aucun rôle » : ce n'est pas la même chose,
             et la différence compte au moment de décider d'un accès. */
          if (m) { id.roles = m.roles || []; if (m.nick) id.nick = m.nick; }
          try { localStorage.setItem(CLE_IDENT, JSON.stringify(id)); } catch (e) {}
          return id;
        });
      })
      .catch(function () { return identiteLocale(); });
  }

  /* Rôles de la personne SUR LE SERVEUR — lus avec le même jeton, qui est
     ensuite oublié comme le reste. Renvoie null si l'information n'est pas
     disponible, plutôt que de faire passer un doute pour un refus. */
  function rolesServeur(tok) {
    if (!SERVEUR) return Promise.resolve(null);
    return fetch("https://discord.com/api/users/@me/guilds/" + encodeURIComponent(SERVEUR) + "/member",
                 { headers: { Authorization: "Bearer " + tok } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (m) { return m ? { roles: (m.roles || []).map(String), nick: m.nick || "" } : null; })
      .catch(function () { return null; });
  }
  function identiteLocale() {
    try { return JSON.parse(localStorage.getItem(CLE_IDENT) || "null"); } catch (e) { return null; }
  }
  function oublierIdentite() { try { localStorage.removeItem(CLE_IDENT); } catch (e) {} }

  /* ============================================================
     ÉMULATION DE L'API SUPABASE POUR LES TABLES ANNEXES
     Les tables vivent dans l'état partagé, sous _tables.
     On reproduit la partie de l'API réellement utilisée par le
     dashboard, pour ne modifier AUCUN des appels existants.
     ============================================================ */
  /* Les logs du bot ne vivent pas dans l'état : ils sont collectés toutes les
     15 min par le robot GitHub dans data/discord-logs.json. On les expose sous
     le nom de table attendu par le dashboard, avec les champs qu'il attend. */
  var LOGS = { charges: false, lignes: [] };
  function chargerLogsBot() {
    if (LOGS.charges) return Promise.resolve(LOGS.lignes);
    return fetch("data/discord-logs.json?t=" + Date.now(), { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        var msgs = (j && j.messages) || [];
        LOGS.lignes = msgs.map(function (m) {
          return {
            id: m.id, ts: m.t, type: m.type || "", employe: m.nom || m.auteur || "",
            details: m.texte || "",
            /* le nom du coffre remonte tel quel : c'est sur lui que filtre la vue */
            coffre: m.coffre || "",
            meta: {
              auteur: m.auteur, quantite: m.quantite, montant: m.montant,
              coffre: m.coffre || undefined, salon: m.salon || undefined,
              champs: m.champs || undefined
            }
          };
        });
        LOGS.charges = true;
        return LOGS.lignes;
      })
      .catch(function () { LOGS.charges = true; return LOGS.lignes; });
  }

  function creerClient(hooks) {
    function table(nom) {
      if (nom === "oilroxwood_bot_logs") return LOGS.lignes;
      var S = hooks.etat();
      S._tables = S._tables || {};
      S._tables[nom] = S._tables[nom] || [];
      return S._tables[nom];
    }

    function Requete(nom) {
      this.nom = nom; this.filtres = []; this.action = "select";
      this.charge = null; this.tri = null; this.limite = 0; this.unique = false;
    }
    Requete.prototype.select = function () { if (this.action === "select") this.action = "select"; return this; };
    Requete.prototype.eq = function (col, val) { this.filtres.push([col, val, "="]); return this; };
    Requete.prototype.is = function (col, val) { this.filtres.push([col, val, "="]); return this; };
    Requete.prototype.neq = function (col, val) { this.filtres.push([col, val, "!="]); return this; };
    Requete.prototype.gte = function (col, val) { this.filtres.push([col, val, ">="]); return this; };
    Requete.prototype.lte = function (col, val) { this.filtres.push([col, val, "<="]); return this; };
    Requete.prototype.gt  = function (col, val) { this.filtres.push([col, val, ">"]);  return this; };
    Requete.prototype.lt  = function (col, val) { this.filtres.push([col, val, "<"]);  return this; };
    Requete.prototype.in  = function (col, arr) { this.filtres.push([col, arr, "in"]); return this; };
    Requete.prototype.order = function (col, o) { this.tri = [col, !(o && o.ascending === false)]; return this; };
    Requete.prototype.limit = function (n) { this.limite = n; return this; };
    Requete.prototype.maybeSingle = function () { this.unique = true; return this; };
    Requete.prototype.single = function () { this.unique = true; return this; };
    Requete.prototype.insert = function (l) { this.action = "insert"; this.charge = l; return this; };
    Requete.prototype.upsert = function (l) { this.action = "upsert"; this.charge = l; return this; };
    Requete.prototype.update = function (l) { this.action = "update"; this.charge = l; return this; };
    Requete.prototype.delete = function () { this.action = "delete"; return this; };

    Requete.prototype.correspond = function (r) {
      return this.filtres.every(function (f) {
        var col = f[0], val = f[1], op = f[2] || "=";
        var i = col.indexOf("->>");                       // ex. "data->>_rev"
        var v = i > 0 ? ((r[col.slice(0, i)] || {})[col.slice(i + 3)]) : r[col];
        if (op === "in") return [].concat(val).some(function (x) { return String(x) === String(v); });
        if (op === "=")  return val === null ? (v === null || v === undefined) : String(v) === String(val);
        if (op === "!=") return String(v) !== String(val);
        if (v === null || v === undefined) return false;
        if (op === ">=") return v >= val;
        if (op === "<=") return v <= val;
        if (op === ">")  return v > val;
        if (op === "<")  return v < val;
        return true;
      });
    };

    Requete.prototype.executer = function () {
      var t = table(this.nom), self = this, res = [], modifie = false;
      try {
        if (this.action === "select") {
          res = t.filter(function (r) { return self.correspond(r); });
          if (this.tri) {
            var c = this.tri[0], asc = this.tri[1];
            res = res.slice().sort(function (a, b) {
              return (a[c] > b[c] ? 1 : a[c] < b[c] ? -1 : 0) * (asc ? 1 : -1);
            });
          }
          if (this.limite) res = res.slice(0, this.limite);
        } else if (this.action === "insert" || this.action === "upsert") {
          var lignes = [].concat(this.charge);
          lignes.forEach(function (l) {
            var copie = Object.assign({}, l);
            var cles = Object.keys(copie).filter(function (k) { return k === "id" || k === "did"; });
            var idx = -1;
            if (cles.length) {
              idx = t.findIndex(function (r) {
                return cles.every(function (k) { return String(r[k]) === String(copie[k]); });
              });
            }
            if (idx >= 0) {
              if (self.action === "upsert") { Object.assign(t[idx], copie); res.push(t[idx]); modifie = true; }
              else throw Object.assign(new Error("duplicate key"), { code: "23505" });
            } else {
              if (copie.id === undefined) copie.id = Date.now() + Math.floor(Math.random() * 1000);
              t.push(copie); res.push(copie); modifie = true;
            }
          });
        } else if (this.action === "update") {
          t.forEach(function (r) {
            if (self.correspond(r)) { Object.assign(r, self.charge); res.push(r); modifie = true; }
          });
        } else if (this.action === "delete") {
          for (var i = t.length - 1; i >= 0; i--) {
            if (self.correspond(t[i])) { res.push(t[i]); t.splice(i, 1); modifie = true; }
          }
        }
      } catch (e) {
        return Promise.resolve({ data: null, error: e });
      }
      if (modifie) hooks.modifie();
      var d = this.unique ? (res[0] || null) : res;
      return Promise.resolve({ data: d, error: null });
    };
    Requete.prototype.then = function (ok, ko) {
      var self = this;
      // les logs du bot viennent d'un fichier : on l'attend avant de filtrer
      if (this.nom === "oilroxwood_bot_logs")
        return chargerLogsBot().then(function () { return self.executer(); }).then(ok, ko);
      return this.executer().then(ok, ko);
    };

    return {
      from: function (nom) { return new Requete(nom); },
      /* les canaux temps réel n'existent pas sans serveur : on les avale poliment */
      channel: function () {
        var faux = { on: function () { return faux; }, subscribe: function (cb) { if (cb) cb("SUBSCRIBED"); return faux; }, send: function () {} };
        return faux;
      },
      removeChannel: function () {},
      auth: {
        onAuthStateChange: function () { return { data: { subscription: { unsubscribe: function () {} } } }; },
        getSession: function () { return Promise.resolve({ data: { session: null } }); },
        signInWithOAuth: function () { connexionDiscord(); return Promise.resolve({}); },
        signOut: function () { oublierIdentite(); return Promise.resolve({}); }
      }
    };
  }

  global.RoxwoodGH = {
    CFG: CFG,
    lire: lire,
    lireAvecSha: lireAvecSha,
    verifierAcces: verifierAcces,
    ecrire: ecrire,
    jeton: jeton,
    poserJeton: poserJeton,
    televerser: televerser,
    supprimerFichier: supprimerFichier,
    peutEcrire: peutEcrire,
    connexionDiscord: connexionDiscord,
    configurerServeur: configurerServeur,
    serveur: serveur,
    recupererIdentite: recupererIdentite,
    identiteLocale: identiteLocale,
    oublierIdentite: oublierIdentite,
    creerClient: creerClient
  };
})(window);
