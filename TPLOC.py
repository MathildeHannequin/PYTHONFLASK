import os
import numpy as np
from PIL import Image
import io
import base64
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering
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
                nom_methode = "Hiérarchique (CAH)" # Mise à jour si c'est HC
            else:
                model = KMeans(n_clusters=k, n_init=10)
                nom_methode = "K-Means" # Mise à jour si c'est KMeans


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

if __name__ == '__main__':
    app.run(debug=True, port=5001)