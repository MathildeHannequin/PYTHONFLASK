import os
import numpy as np
from PIL import Image
import io
import base64
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import DBSCAN
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('Apropos.html')

@app.route('/map')
def map_view():
    return render_template('ma_carte.html')

REPERTOIRE_PAR_DEFAUT = "C:/Users" 

@app.route('/galerie', methods=['GET', 'POST'])
def galerie():
    if request.method == 'POST':
        chemin_dossier = request.form.get('chemin', REPERTOIRE_PAR_DEFAUT)
    else:
        chemin_dossier = request.args.get('chemin', REPERTOIRE_PAR_DEFAUT)
    
    images = []
    erreur = None

    if os.path.exists(chemin_dossier):
        images = [f for f in os.listdir(chemin_dossier) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    else:
        erreur = "Le répertoire est introuvable."

    image_choisie = request.args.get('image_selectionnee')
    
    return render_template('galerie.html', 
                           images=images, 
                           image_choisie=image_choisie, 
                           chemin=chemin_dossier,
                           erreur=erreur)

@app.route('/image_brute/<path:nom_image>')
def image_brute(nom_image):
    dossier = request.args.get('dossier')
    return send_from_directory(dossier, nom_image)

@app.route('/executer_segmentation')
def executer_segmentation():
    chemin_dossier = request.args.get('chemin')
    nom_image = request.args.get('image_selectionnee')
    k = request.args.get('k', 5, type=int)
    methode = request.args.get('methode', 'kmeans')
    
    nom_methode = "K-Means" 
    image_base64 = None

    if chemin_dossier and nom_image:
        try:
            img = Image.open(os.path.join(chemin_dossier, nom_image)).convert('RGB')
            
            taille_max = 100 if methode == 'hc' else 300
            img.thumbnail((taille_max, taille_max))
            
            img_np = np.array(img)
            h, w, c = img_np.shape
            pixels = img_np.reshape(-1, c)

            if methode == 'hc':
                model = AgglomerativeClustering(n_clusters=k, metric='euclidean', linkage='complete')
                nom_methode = "Hiérarchique (CAH)" #si c'est HC
            else:
                model = KMeans(n_clusters=k, n_init=10)
                nom_methode = "K-Means" #si c'est KMeans


            labels = model.fit_predict(pixels)

            if methode == 'hc':
                centres = np.array([pixels[labels == i].mean(axis=0) for i in range(k)]).astype(np.uint8)
            else:
                centres = model.cluster_centers_.astype(np.uint8)
            
            img_reconstruite = centres[labels].reshape(h, w, c)

            res_pil = Image.fromarray(img_reconstruite)
            tampon = io.BytesIO()
            res_pil.save(tampon, format="PNG")
            image_base64 = f"data:image/png;base64,{base64.b64encode(tampon.getvalue()).decode('utf-8')}"
            
        except Exception as e:
            print(f"Erreur lors de la segmentation : {e}")

    return render_template('segmentation.html', 
                           nom_image=nom_image, 
                           k=k,
                           image_data=image_base64,
                           chemin=chemin_dossier,
                           methode=nom_methode)

@app.route('/segmentation_dbscan')
def segmentation_dbscan():
    chemin_dossier = request.args.get('chemin')
    nom_image = request.args.get('image_selectionnee')
    
    eps = request.args.get('eps', 5.0, type=float)
    min_samples = request.args.get('min_samples', 10, type=int)
    
    image_base64 = None

    if chemin_dossier and nom_image:
        try:
            img = Image.open(os.path.join(chemin_dossier, nom_image)).convert('RGB')
            img.thumbnail((150, 150))
            img_np = np.array(img)
            h, w, c = img_np.shape
            pixels = img_np.reshape(-1, c)

            db = DBSCAN(eps=eps, min_samples=min_samples)
            labels = db.fit_predict(pixels)

            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            
            centres = np.zeros((len(set(labels)), 3), dtype=np.uint8)
            for i in set(labels):
                if i == -1:
                    centres[i] = [0, 0, 0] 
                else:
                    centres[i] = pixels[labels == i].mean(axis=0)
            
            img_reconstruite = centres[labels].reshape(h, w, c)

            res_pil = Image.fromarray(img_reconstruite)
            tampon = io.BytesIO()
            res_pil.save(tampon, format="PNG")
            image_base64 = f"data:image/png;base64,{base64.b64encode(tampon.getvalue()).decode('utf-8')}"
            
        except Exception as e:
            print(f"Erreur DBSCAN : {e}")

    return render_template('dbscan.html', 
                           nom_image=nom_image, 
                           eps=eps, 
                           min_samples=min_samples,
                           image_data=image_base64, 
                           chemin=chemin_dossier)

if __name__ == '__main__':
    app.run(debug=True, port=5001)