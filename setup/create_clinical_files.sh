#!/bin/bash

# Directory where files will be created
TARGET_DIR="/home/station-clinique01/medical_records"

# Create the target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Number of files to create
NUM_FILES=100

# Base date for file timestamps (e.g., starting from today)
BASE_DATE=$(date +%Y-%m-%d)

# Arrays of sample data
PRENOMS=(
  "JEAN" "LOUIS" "PIERRE" "JOSEPH" "HENRI" "MARCEL" "GEORGES" "ANDRÉ" "PAUL" "RENÉ"
  "CHARLES" "FRANÇOIS" "EMILE" "MAURICE" "ALBERT" "EUGÈNE" "JOSEPHINE" "LÉON" "HENRIETTE"
  "LUCIEN" "JULES" "AUGUSTE" "GEORGETTE" "ROBERT" "LUCIENNE" "JULIETTE" "FERNAND" "GASTON"
  "RAYMOND" "ANTOINE" "ROGER" "ANNA" "MARIUS" "ALFRED" "ANTOINETTE" "VICTOR" "ERNEST"
  "JULIEN" "GABRIEL" "ALPHONSE" "CAMILLE" "JACQUES" "PAULINE" "EDOUARD" "LÉONTINE"
  "CHARLOTTE" "MARIE" "MARIE-LOUISE" "GUSTAVE" "ADRIENNE" "EDMOND" "ALEXANDRE" "EMILIENNE"
  "ETIENNE" "ALBERTINE" "JULIA" "ADRIEN" "FÉLIX" "ARMAND" "MICHEL" "CLEMENCE" "VALENTINE"
  "ALINE" "YVES" "ERNESTINE" "CLAUDE" "ARTHUR" "RAOUL" "CLÉMENCE" "ELIE" "LEONIE"
  "ALPHONSINE" "AIME" "AUGUSTIN" "FRÉDÉRIC" "CLÉMENTINE" "GERMAIN" "CLÉMENT" "ADOLPHE"
  "DÉSIRÉ" "ELISA" "FRANCINE" "CAROLINE" "JANIQUE" "FRANCIS" "FERDINAND" "FELICIE"
  "GUILLAUME" "ABEL" "BERNARD" "ALEXANDRINE" "PHILIPPE" "LEANE" "LEANA" "NICOLAS"
  "ANTONIN" "GILBERT" "LAURENT" "LEOPOLD" "JOFFRETTE" "ALEXIS" "DANIEL" "MARC"
  "CLAUDINE" "CONSTANT" "EMMANUEL" "NOËL" "THEOPHILE" "MAXIME" "CLAUDIUS" "SALOME"
  "ADELE" "JEAN-BAPTISTE" "MARIE-THÉRÈSE" "CELESTIN" "VINCENT" "JUSTIN" "MARCEAU"
  "OCTAVE" "GILBERTE" "VICTORIA" "ARSENE" "BAPTISTE" "HELOISE" "DOMINIQUE" "TIMOTHEE"
  "LEON" "MAGDELEINE" "CLAUDIA" "ANAÏS" "MARTIN" "NOEMIE" "BENOÎT" "CLEMENTINE"
  "FIRMIN" "NOELIE" "THEODORE" "MARCELLINE" "HIPPOLYTE" "ANNETTE" "LEONARD" "ADELINE"
  "GAETAN" "BERNADETTE" "CELINA" "OCTAVIE" "HUBERT" "MARTIAL" "DENIS" "ACHILLE"
  "AMEDEE" "EMILIEN" "CLEA" "MARCELINE" "LEONCE" "LEANDRE" "ARMANDINE" "TEO"
  "SIMON" "PAULETTE" "HONORE" "RAPHAËL" "ANGELINE" "MAHE" "PROSPER"
)

NOMS=(
  "Martin" "Bernard" "Thomas" "Petit" "Robert" "Richard" "Durand" "Dubois" "Moreau" "Laurent"
  "Simon" "Michel" "Lefebvre" "Leroy" "Roux" "David" "Bertrand" "Morel" "Fournier" "Girard"
  "Bonnet" "Dupont" "Lambert" "Fontaine" "Rousseau" "Vincent" "Muller" "Lefevre" "Faure" "Andre"
  "Mercier" "Blanc" "Guerin" "Boyer" "Garnier" "Chevalier" "Francois" "Legrand" "Gauthier" "Garcia"
  "Perrin" "Robin" "Clement" "Morin" "Nicolas" "Henry" "Roussel" "Mathieu" "Gautier" "Masson"
  "Marchand" "Duval" "Denis" "Dumont" "Marie" "Lemoine" "Noel" "Meyer" "Dufour" "Meunier"
  "Brun" "Blanchard" "Giraud" "Joly" "Riviere" "Lucas" "Brunet" "Gaillard" "Barbier" "Arnaud"
  "Martinez" "Gerard" "Roche" "Renard" "Schmitt" "Roy" "Leroux" "Colin" "Vidal" "Caron"
  "Picard" "Roger" "Fabre" "Aubert" "Lemoine" "Renaud" "Dumas" "Lacroix" "Olivier" "Philippe"
  "Bourgeois" "Pierre" "Benoit" "Rey" "Leclerc" "Payet" "Rolland" "Leclercq" "Guillaume" "Lecomte"
)

DIAGNOSES=(
  "Hypertension"
  "Diabète de type 2"
  "Maladie pulmonaire obstructive chronique"
  "Maladie coronarienne"
  "Arthrose"
  "Asthme"
  "Maladie rénale chronique"
  "Insuffisance cardiaque"
  "Dépression"
  "Trouble anxieux"
  "Migraine"
  "Épilepsie"
  "Maladie de Parkinson"
  "Sclérose en plaques"
  "Polyarthrite rhumatoïde"
  "Lupus"
  "Psoriasis"
  "Maladie cœliaque"
  "Maladie de Crohn"
  "Rectocolite hémorragique"
  "Cancer du sein"
  "Cancer du poumon"
  "Cancer de la prostate"
  "Cancer colorectal"
  "Hépatite B"
  "Hépatite C"
  "VIH/SIDA"
  "Tuberculose"
  "Grippe"
  "Pneumonie"
  "Bronchite chronique"
  "Anémie"
  "Leucémie"
  "Lymphome"
  "Maladie d'Alzheimer"
  "Démence"
  "Syndrome de l'intestin irritable"
  "Gastrite"
  "Ulcère gastrique"
  "Insuffisance rénale"
  "Hypercholestérolémie"
  "Hypothyroïdie"
  "Hyperthyroïdie"
  "Obésité"
  "Syndrome métabolique"
  "Goutte"
  "Syndrome des jambes sans repos"
  "Apnée du sommeil"
  "Syndrome de fatigue chronique"
  "Fibromyalgie"
)

TREATMENTS=(
  "Lisinopril 10 mg"
  "Metformine 500 mg"
  "Salbutamol 100 µg"
  "Atorvastatine 20 mg"
  "Ibuprofène 400 mg"
  "Insuline 10 UI"
  "Amlodipine 5 mg"
  "Oméprazole 20 mg"
  "Sertraline 50 mg"
  "Fluoxétine 20 mg"
  "Aspirine 100 mg"
  "Clopidogrel 75 mg"
  "Warfarine 5 mg"
  "Amoxicilline 500 mg"
  "Azithromycine 250 mg"
  "Ciprofloxacine 500 mg"
  "Doxycycline 100 mg"
  "Hydrochlorothiazide 25 mg"
  "Furosémide 40 mg"
  "Spironolactone 25 mg"
  "Paracétamol 500 mg"
  "Tramadol 50 mg"
  "Morphine 10 mg"
  "Codéine 30 mg"
  "Prednisone 10 mg"
  "Hydrocortisone 20 mg"
  "Méthotrexate 10 mg"
  "Adalimumab 40 mg"
  "Infliximab 100 mg"
  "Rituximab 500 mg"
  "Lévothyroxine 50 µg"
  "Carbimazole 5 mg"
  "Metoprolol 50 mg"
  "Propranolol 40 mg"
  "Losartan 50 mg"
  "Valsartan 80 mg"
  "Simvastatine 20 mg"
  "Rosuvastatine 10 mg"
  "Ezetimibe 10 mg"
  "Clarithromycine 500 mg"
  "Dexaméthasone 4 mg"
  "Cétirizine 10 mg"
  "Loratadine 10 mg"
  "Pantoprazole 40 mg"
  "Esoméprazole 20 mg"
  "Ranitidine 150 mg"
  "Famotidine 20 mg"
  "Alendronate 70 mg"
  "Risedronate 35 mg"
  "Denosumab 60 mg"
  "Teriparatide 20 µg"
  "Calcitonine 200 UI"
  "Vitamine D 1000 UI"
  "Calcium 500 mg"
  "Fer 100 mg"
  "Acide folique 5 mg"
  "Vitamine B12 1000 µg"
  "Thiamine 100 mg"
  "Riboflavine 10 mg"
  "Niacine 50 mg"
  "Pyridoxine 25 mg"
  "Biotine 5 mg"
  "Acide pantothénique 100 mg"
  "Vitamine C 500 mg"
  "Vitamine E 400 UI"
  "Vitamine K 10 mg"
)

# Function to generate random content for a file
generate_content() {
    local prenom=${PRENOMS[$RANDOM % ${#PRENOMS[@]}]}
    local nom=${NOMS[$RANDOM % ${#NOMS[@]}]}
    local diagnosis=${DIAGNOSES[$RANDOM % ${#DIAGNOSES[@]}]}
    local treatment=${TREATMENTS[$RANDOM % ${#TREATMENTS[@]}]}
    local date=$(date +%Y-%m-%d)
    
    # Array of different notes in French
    local notes=(
        "Suivi dans 2 semaines."
        "Revenir pour un contrôle dans un mois."
        "Prendre le médicament tous les jours."
        "Faire des exercices physiques régulièrement."
        "Éviter les aliments gras et sucrés."
        "Boire beaucoup d'eau."
        "Surveiller la tension artérielle quotidiennement."
        "Consulter un spécialiste si les symptômes persistent."
        "Faire une prise de sang dans une semaine."
        "Revoir le traitement si les effets secondaires apparaissent."
        "Suivre un régime alimentaire équilibré."
        "Éviter le stress autant que possible."
        "Prendre rendez-vous pour une échographie."
        "Faire une radiographie si la douleur persiste."
        "Revenir pour un contrôle dans 3 mois."
        "Prendre les médicaments avec de la nourriture."
        "Éviter l'alcool pendant le traitement."
        "Faire des analyses de sang tous les 3 mois."
        "Consulter un nutritionniste pour un régime adapté."
        "Revoir le médecin traitant pour un suivi régulier."
        "Prescrire un bilan complet."
        "Planifier une visite de contrôle."
        "Examiner d'éventuelles complications."
        "Réaliser un test de laboratoire approfondi."
        "Mettre à jour le dossier médical après consultation."
        "Confirmer les résultats avec un spécialiste."
        "Vérifier régulièrement la qualité de vie."
        "Adapter le traitement en fonction des nouveaux symptômes."
        "Effectuer un examen spécialisé rapidement."
    )
    
    local note=${notes[$RANDOM % ${#notes[@]}]}
    
    echo "Nom du patient: $prenom $nom"
    echo "Date: $date"
    echo "Diagnostic: $diagnosis"
    echo "Traitement: $treatment"
    echo "Notes: $note"
}

# Loop to create files
for i in $(seq 1 $NUM_FILES); do
  # Generate a filename with a specific pattern
  FILENAME="$TARGET_DIR/file_$i.txt"
  
  # Generate a date for the file (e.g., incrementing days)
  FILE_DATE=$(date -d "$BASE_DATE +$i day" +%Y-%m-%d)
  
  # Create the file with specific content
  generate_content > "$FILENAME"
  
  # Set the file's modification time to the generated date
  touch -d "$FILE_DATE" "$FILENAME"
  
  echo "Created $FILENAME with date $FILE_DATE in $TARGET_DIR"
done

echo "All files created successfully."