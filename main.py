import tkinter as tk
from tkinter import ttk
import geopandas as gpd
import pandas as pd
import folium
import webbrowser
import os

# === 1. CHARGER LES DONNÉES ===
print("📥 Chargement des données...")
url_paris = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson"
paris_geo = gpd.read_file(url_paris)

# Données de risques
risques_data = {
    'c_ar': [75101, 75102, 75103, 75104, 75105, 75106, 75107, 75108, 75109, 75110,
             75111, 75112, 75113, 75114, 75115, 75116, 75117, 75118, 75119, 75120],
    'agressions': [12, 15, 8, 10, 5, 7, 3, 9, 14, 11, 16, 8, 10, 6, 4, 3, 12, 18, 9, 11],
    'incendies': [2, 3, 1, 2, 1, 2, 1, 3, 2, 1, 3, 2, 1, 2, 1, 1, 2, 3, 1, 2],
    'accidents_voiture': [34, 42, 28, 31, 15, 22, 18, 38, 40, 25, 45, 30, 32, 20, 19, 16, 35, 48, 22, 26]
}

df_risques = pd.DataFrame(risques_data)
gdf_complet = paris_geo.merge(df_risques, on='c_ar', how='left')

print(f"✅ {len(gdf_complet)} arrondissements chargés")

# === 2. CLASSE APPLICATION ===
class AppCarteParis:
    def __init__(self, root, gdf, df_risques):
        self.root = root
        self.gdf = gdf
        self.df_risques = df_risques
        
        self.root.title("🗺️  Carte des Risques - Métropole Parisienne")
        self.root.geometry("1000x600")
        self.root.configure(bg='#f0f0f0')
        
        # === FRAME SUPÉRIEUR (Contrôles) ===
        frame_top = tk.Frame(root, bg='#2c3e50', height=80)
        frame_top.pack(fill=tk.X)
        
        tk.Label(frame_top, text="🗺️  Carte des Risques - Métropole Parisienne", 
                font=('Arial', 14, 'bold'), fg='white', bg='#2c3e50').pack(pady=10)
        
        control_frame = tk.Frame(frame_top, bg='#2c3e50')
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Sélecteur de risque
        tk.Label(control_frame, text="📊 Type de risque :", 
                font=('Arial', 10), fg='white', bg='#2c3e50').pack(side=tk.LEFT, padx=(0, 10))
        
        self.risque_var = tk.StringVar(value="agressions")
        self.combo_risque = ttk.Combobox(
            control_frame,
            textvariable=self.risque_var,
            values=['agressions', 'incendies', 'accidents_voiture'],
            state='readonly',
            width=20
        )
        self.combo_risque.pack(side=tk.LEFT, padx=(0, 20))
        
        # Seuil d'alerte
        tk.Label(control_frame, text="⚠️  Seuil d'alerte :", 
                font=('Arial', 10), fg='white', bg='#2c3e50').pack(side=tk.LEFT, padx=(0, 10))
        
        self.seuil_var = tk.IntVar(value=10)
        seuil_scale = ttk.Scale(control_frame, from_=0, to=50, variable=self.seuil_var, orient=tk.HORIZONTAL)
        seuil_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.seuil_label = tk.Label(control_frame, text="10", font=('Arial', 10, 'bold'), 
                                   fg='white', bg='#2c3e50', width=3)
        self.seuil_label.pack(side=tk.LEFT)
        
        self.seuil_var.trace('w', lambda *args: self.seuil_label.config(text=str(self.seuil_var.get())))
        
        # Bouton générer
        ttk.Button(control_frame, text="🔄 Générer Carte", 
                  command=self.generer_carte).pack(side=tk.LEFT, padx=(20, 0))
        
        # === FRAME PRINCIPAL (Contenu) ===
        main_frame = tk.Frame(root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # GAUCHE : Message + Bouton
        left_frame = tk.Frame(main_frame, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(left_frame, text="🌐 Carte Interactive", 
                font=('Arial', 12, 'bold'), bg='white').pack(pady=10)
        
        msg_text = """La carte Folium s'affiche dans votre navigateur.

✨ Fonctionnalités :
  • Zoom interactif
  • Déplacement de la carte
  • Popups informatifs
  • Couches superposables

Cliquez sur le bouton pour générer 
et afficher la carte."""
        
        tk.Label(left_frame, text=msg_text, justify=tk.LEFT, bg='white', 
                font=('Arial', 9), wraplength=300).pack(pady=20, padx=20)
        
        ttk.Button(left_frame, text="🌍 Ouvrir Carte dans Navigateur", 
                  command=self.ouvrir_derniere_carte).pack(pady=10)
        
        # DROITE : Statistiques
        right_frame = tk.Frame(main_frame, bg='#ecf0f1', relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 0), pady=0, anchor='n')
        
        tk.Label(right_frame, text="📊 Statistiques", font=('Arial', 12, 'bold'), 
                bg='#ecf0f1').pack(pady=10)
        
        # Créer les stats pour chaque risque
        stats_frame = tk.Frame(right_frame, bg='white')
        stats_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        for risque in ['agressions', 'incendies', 'accidents_voiture']:
            min_val = df_risques[risque].min()
            max_val = df_risques[risque].max()
            mean_val = df_risques[risque].mean()
            
            risque_label = risque.replace('_', ' ').title()
            
            tk.Label(stats_frame, text=risque_label, font=('Arial', 10, 'bold'), 
                    bg='white', fg='#2c3e50').pack(anchor='w', pady=(10, 5))
            
            stats_det = f"  Min: {min_val}  |  Max: {max_val}  |  Moy: {mean_val:.1f}"
            tk.Label(stats_frame, text=stats_det, font=('Courier', 8), 
                    bg='white', fg='#555').pack(anchor='w', pady=(0, 5))
        
        # === FOOTER ===
        footer = tk.Frame(root, bg='#34495e', height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(footer, text="✅ Prêt", font=('Arial', 9), 
                                    bg='#34495e', fg='#2ecc71')
        self.status_label.pack(pady=10)
        
        self.derniere_carte = None
    
    def generer_carte(self):
        """Génère et ouvre la carte Folium"""
        risque = self.risque_var.get()
        seuil = self.seuil_var.get()
        
        self.status_label.config(text=f"🔄 Génération en cours...", fg='#f39c12')
        self.root.update()
        
        # Créer la carte
        centre_paris = [48.8566, 2.3522]
        carte = folium.Map(location=centre_paris, zoom_start=12, tiles='CartoDB positron')
        
        # Choroplèthe
        folium.Choropleth(
            geo_data=self.gdf.to_json(),
            name=risque.replace('_', ' ').title(),
            data=self.gdf,
            columns=['c_ar', risque],
            key_on='feature.properties.c_ar',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name=risque.replace('_', ' ').title()
        ).add_to(carte)
        
        # Marquer zones critiques
        for idx, row in self.gdf.iterrows():
            if pd.notna(row[risque]) and row[risque] > seuil:
                folium.CircleMarker(
                    location=[row.geometry.centroid.y, row.geometry.centroid.x],
                    radius=12,
                    color='red',
                    fill=True,
                    fill_color='red',
                    fill_opacity=0.7,
                    popup=f"<b>🚨 {row['l_ar']}</b><br>{risque}: {row[risque]} (CRITIQUE)",
                    tooltip="Zone à risque élevé"
                ).add_to(carte)
        
        folium.LayerControl().add_to(carte)
        
        # Sauvegarder
        nom_fichier = f'carte_{risque}_seuil{seuil}.html'
        carte.save(nom_fichier)
        self.derniere_carte = os.path.abspath(nom_fichier)
        
        # Ouvrir
        webbrowser.open(self.derniere_carte)
        
        self.status_label.config(text=f"✅ Carte '{risque}' générée et ouverte !", fg='#2ecc71')
    
    def ouvrir_derniere_carte(self):
        """Ouvre la dernière carte générée"""
        if self.derniere_carte and os.path.exists(self.derniere_carte):
            webbrowser.open(self.derniere_carte)
            self.status_label.config(text="🌍 Carte ouverte", fg='#2ecc71')
        else:
            self.status_label.config(text="⚠️ Aucune carte générée. Générez d'abord.", fg='#e74c3c')

# === LANCER ===
root = tk.Tk()
app = AppCarteParis(root, gdf_complet, df_risques)
root.mainloop()
