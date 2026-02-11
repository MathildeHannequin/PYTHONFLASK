import os
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return """
    <h1>À propos de moi</h1>
    <p>Je suis en train d'apprendre à développer des applications web avec Flask.</p>
    <a href="/">Retour à l'accueil</a>
    """

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

@app.route('/segmentation')
def segmentation():
    chemin_dossier = request.args.get('chemin')
    nom_image = request.args.get('image_selectionnee')
    k_clusters = request.args.get('k', 5, type=int) 
    
    image_segmentee_url = None

    if chemin_dossier and nom_image:
        chemin_complet = os.path.join(chemin_dossier, nom_image)
        
        img = Image.open(chemin_complet).convert('RGB')
        img_np = np.array(img)
        h, w, c = img_np.shape
        
        pixels = img_np.reshape(-1, c)
        print(pixels.shape)
        
        kmeans = KMeans(n_clusters=k_clusters, n_init=10)
        labels = kmeans.fit_predict(pixels)
        
        centres = kmeans.cluster_centers_.astype(np.uint8)
        img_reconstruite = centres[labels].reshape(h, w, c)
        
        res_pil = Image.fromarray(img_reconstruite)
        nom_fichier_resultat = "temp_segmentation.png"
        res_pil.save(os.path.join('static', nom_fichier_resultat))
        image_segmentee_url = nom_fichier_resultat

    return render_template('segmentation.html', 
                           chemin=chemin_dossier, 
                           nom_image=nom_image, 
                           k=k_clusters,
                           resultat=image_segmentee_url)


if __name__ == '__main__':
    app.run(debug=True, port=5001)


