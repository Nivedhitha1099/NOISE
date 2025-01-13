from flask import Flask, request, jsonify, render_template
import os
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from collections import Counter
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def calculate_similarity(fragment_structure, class_structure):
    fragment_counter = Counter({k: v.get('value', 0) for k, v in fragment_structure.items()})
    class_counter = Counter({k: v.get('value', 0) for k, v in class_structure.items()})
    
    logger.debug(f"Fragment structure: {json.dumps(fragment_structure, indent=2)}")
    logger.debug(f"Class structure: {json.dumps(class_structure, indent=2)}")
    
    logger.debug(f"Fragment counter: {dict(fragment_counter)}")
    logger.debug(f"Class counter: {dict(class_counter)}")
    
    common_keys = set(fragment_counter.keys()) & set(class_counter.keys())
    total_keys = set(fragment_counter.keys()) | set(class_counter.keys())
    
    if not total_keys:
        return 0
    
    similarity = len(common_keys) / len(total_keys)
    logger.debug(f"Calculated similarity: {similarity}")
    
    return similarity

def get_recommendations(noise_fragments, clusters):
    recommendations = []
    seen_classes = {} 
    
    for fragment in noise_fragments:
        element_type = fragment.get('element_type')
        fragment_structure = {k: v for k, v in fragment.items() if k.startswith("Level_")}
        recommended_classes = []

        cluster_key = f'cluster_{element_type.lower()}'
        
        if cluster_key in clusters:
            cluster_data = clusters[cluster_key]
            
            if 'classes' in cluster_data:
                for class_name, class_structure in cluster_data['classes'].items():
                     
                    if class_name not in seen_classes:
                        level_structure = {k: v for k, v in class_structure.items() if k.startswith("Level_")}
                        similarity_score = calculate_similarity(fragment_structure, level_structure)
                        
                        
                        first_fragment = next(iter(class_structure.get('fragments', [])), {})
                        
                        recommended_classes.append({
                            'class': class_name,
                            'structure': first_fragment,  
                            'structure_score': similarity_score,
                            'group_key': cluster_key
                        })
                        seen_classes[class_name] = True

        recommended_classes.sort(key=lambda x: x['structure_score'], reverse=True)
        
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

    logger.debug("Uploaded JSON structure:")
    logger.debug(f"Keys in data: {list(data.keys())}")
    logger.debug(f"Number of noise fragments: {len(data.get('noise', []))}")
    logger.debug(f"Number of clusters: {len(data.get('clusters', {}))}")

    noise_fragments = data.get('noise', [])
    clusters = data.get('clusters', {})

    try:
        recommendations = get_recommendations(noise_fragments, clusters)
    except Exception as e:
        logger.exception(f"Error in get_recommendations: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the data. Please check the server logs for more information.'}), 500

    return render_template('noise.html', noise_fragments=noise_fragments, recommendations=recommendations)


    

if __name__ == '__main__':
    app.run(debug=False,port="5003")
