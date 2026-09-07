# SportNews Live — Site d'actualités sportives

Site d'actualités sportives professionnel (style France 24), construit avec **Django** (backend) et **Tailwind CSS** (frontend), pensé pour un seul journaliste/auteur, avec catégorie unique "Sportif", commentaires, images et vidéos.

## Fonctionnalités

- Page d'accueil avec article "à la une" + grille d'articles + pagination + recherche
- Page article détaillée avec image, vidéo (upload ou lien externe type YouTube), contenu
- Commentaires (nom, email, message) sur chaque article
- Interface d'administration Django pour publier/gérer les articles et modérer les commentaires
- Base de données PostgreSQL en ligne (pas de base locale)
- Stockage des images/vidéos sur Cloudinary (gratuit, persistant)
- Prêt à déployer gratuitement sur Render

## 1. Installation en local (pour tester avant de déployer)

```bash
python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Modifie .env : au minimum mets DEBUG=True et laisse DATABASE_URL vide pour tester en local avec sqlite
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ouvre `http://127.0.0.1:8000/` pour le site, et `http://127.0.0.1:8000/admin/` pour publier des articles.

## 2. Créer la base de données en ligne (Supabase — gratuit)

1. Va sur https://supabase.com et crée un compte / un nouveau projet.
2. Dans **Project Settings > Database > Connection string**, choisis l'onglet **URI**.
3. Copie l'URL, elle ressemble à :
   `postgresql://postgres:[MOT-DE-PASSE]@db.xxxxxxxxxxxx.supabase.co:5432/postgres`
4. Colle-la dans la variable `DATABASE_URL` (fichier `.env` en local, et dans les variables d'environnement Render en production).

## 3. Créer le stockage média (Cloudinary — gratuit)

1. Crée un compte sur https://cloudinary.com
2. Dans le Dashboard, récupère : **Cloud name**, **API Key**, **API Secret**.
3. Renseigne-les dans `.env` (`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`) et mets `USE_CLOUDINARY=True`.

> Sans Cloudinary, les images/vidéos uploadées seraient perdues à chaque redéploiement sur Render (stockage non persistant sur le plan gratuit).

## 4. Déployer gratuitement sur Render

1. Mets ton code sur GitHub (crée un repo et pousse le projet).
2. Sur https://render.com, clique **New > Web Service**, connecte ton repo GitHub.
3. Render détecte Python. Configure :
   - **Build Command** : `./build.sh`
   - **Start Command** : `gunicorn sportnews.wsgi:application`
   - **Plan** : Free
4. Dans l'onglet **Environment**, ajoute toutes les variables du fichier `.env.example` (SECRET_KEY, DEBUG=False, ALLOWED_HOSTS avec ton domaine `xxx.onrender.com`, CSRF_TRUSTED_ORIGINS, DATABASE_URL de Supabase, et les 3 variables Cloudinary).
5. Clique **Create Web Service**. Render build et déploie automatiquement.
6. Une fois déployé, crée ton compte admin directement sur le serveur via le Shell Render :
   ```bash
   python manage.py createsuperuser
   ```
7. Va sur `https://ton-site.onrender.com/admin/` pour commencer à publier des articles.

> ⚠️ Sur le plan gratuit Render, le service s'endort après 15 min d'inactivité et met quelques secondes à se réveiller au premier accès — normal, sans coût.

## 5. Générer une SECRET_KEY sécurisée

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Mets le résultat dans `SECRET_KEY` (en local et sur Render).

## Structure du projet

```
sportnews/
├── manage.py
├── requirements.txt
├── build.sh              # script de build pour Render
├── Procfile               # commande de lancement (gunicorn)
├── .env.example            # variables d'environnement à copier en .env
├── sportnews/              # config du projet (settings, urls)
└── articles/               # app principale
    ├── models.py            # Article, Comment
    ├── views.py             # liste, détail, commentaires
    ├── admin.py             # interface d'administration
    └── templates/articles/  # gabarits HTML (Tailwind CDN)
```

## Publier un article

Depuis `/admin/` :
1. Clique sur **Articles > Ajouter**
2. Remplis titre, sous-titre, contenu
3. Ajoute une image de couverture et/ou une vidéo (upload direct ou lien externe)
4. Coche **À la une** pour le mettre en avant sur la page d'accueil
5. Statut = **Publié**

Les commentaires postés par les visiteurs apparaissent automatiquement (modération possible en décochant "Approuvé" dans l'admin).
