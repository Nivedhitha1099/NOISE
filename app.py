from flask import Flask, request, jsonify, render_template
import os
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_recommendations(noise_fragments, clusters):
    recommendations = []
    seen_structures = set()

    for fragment in noise_fragments:
        element_type = fragment.get('element_type')
        fragment_structure = {k: v for k, v in fragment.items() if k.startswith("Level_")}
        recommended_classes = []

        cluster_key = f'cluster_{element_type.lower()}'
        
        if cluster_key in clusters:
            cluster_data = clusters[cluster_key]
            
            if 'classes' in cluster_data:
                for class_name, class_structure in cluster_data['classes'].items():
                    # Extract only Level_ encodings
                    level_structure = {k: v for k, v in class_structure.items() if k.startswith("Level_")}
                    
                    # Create a unique key for the structure
                    structure_key = str(sorted(level_structure.items()))
                    
                    if structure_key not in seen_structures:
                        seen_structures.add(structure_key)
                        recommended_classes.append({
                            'class': class_name,
                            'structure': level_structure,
                            'structure_score': 1.0,
                            'group_key': cluster_key
                        })

        recommendations.append({
            'fragment_id': fragment.get('fragment_id'),
            'element_type': element_type,
            'fragment_structure': fragment_structure,
            'recommendations': recommended_classes
        })

    return recommendations



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-json', methods=['POST'])
def upload_json():
    if 'json_file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    json_file = request.files['json_file']
    if not json_file.filename.endswith('.json'):
        return jsonify({'error': 'Invalid file format. Please upload a JSON file.'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, json_file.filename)
    json_file.save(file_path)

    with open(file_path, 'r') as f:
        data = json.load(f)

    noise_fragments = data.get('noise', [])
    clusters = data.get('clusters', {})

    try:
        recommendations = get_recommendations(noise_fragments, clusters)
    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the data. Please check the server logs for more information.'}), 500

    return render_template('noise.html', noise_fragments=noise_fragments, recommendations=recommendations)


    

if __name__ == '__main__':
    app.run(debug=False,port="5003")