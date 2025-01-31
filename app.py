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
    
    
    logger.debug(f"Fragment structure: {json.dumps(fragment_structure, indent=2)}")
   
    
    logger.debug(f"Fragment counter: {dict(fragment_counter)}")
   
    
    common_keys = set(fragment_counter.keys())
    total_keys = set(fragment_counter.keys()) 
    
    if not total_keys:
        return 0
    
    similarity = len(common_keys) / len(total_keys)
    logger.debug(f"Calculated similarity: {similarity}")
    
    return similarity

def compare_patterns(pattern1, pattern2):
    similarity_score = 0
    for key in pattern1:
        if key in pattern2:
            if pattern1[key] == pattern2[key]:
                similarity_score += 1
    return similarity_score / len(pattern1)

def get_recommendations(noise_fragments, clusters):
    recommendations = []
    seen_classes = {}

    with open('pattern_final12.json') as f:
        pattern_data = json.load(f)

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

                        recommended_classes.append({
                            'class': class_name,
                            'structure': level_structure,
                            'structure_score': similarity_score,
                            'group_key': cluster_key
                        })
                        seen_classes[class_name] = True

        # If no recommendations are found, take the same element type from the pattern file
            if not recommended_classes:
              similar_pattern = None
              max_similarity = 0
              for pattern in pattern_data:
                 similarity = compare_patterns(fragment_structure, pattern)
                 if similarity > max_similarity:
                      max_similarity = similarity
                      similar_pattern = pattern
              if similar_pattern:
                      recommended_classes.append({
                'class': similar_pattern['class'],
                'structure': similar_pattern['structure'],
                'structure_score': max_similarity,
                'group_key': cluster_key
            })
    
    return recommended_classes

    

@app.route('/')
def index():
    return render_template('index.html')

from datetime import datetime
from datetime import datetime

# ... (keep existing imports and other code)

@app.route('/upload-json', methods=['POST'])
def upload_json():
    if 'json_file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    json_file = request.files['json_file']
    if not json_file.filename.endswith('.json'):
        return jsonify({'error': 'Invalid file format. Please upload a JSON file.'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, json_file.filename)
    json_file.save(file_path)

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        logger.debug("Uploaded JSON structure:")
        logger.debug(f"Keys in data: {list(data.keys())}")
        logger.debug(f"Number of noise fragments: {len(data.get('noise', []))}")
        logger.debug(f"Number of clusters: {len(data.get('clusters', {}))}")

        noise_fragments = data.get('noise', [])
        clusters = data.get('clusters', {})

        recommendations = get_recommendations(noise_fragments, clusters)

        # Wrap noise fragments and recommendations in a new "noises" key
        updated_data = {
            'noises': [
                {
                    'noise': fragment,
                    'recommendations': recommendations
                }
                for fragment in noise_fragments
            ]
        }

        
        output_folder = 'output'
        os.makedirs(output_folder, exist_ok=True)

        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"recommendations_{timestamp}.json"
        output_path = os.path.join(output_folder, output_filename)

        
        with open(output_path, 'w') as f:
            json.dump(updated_data, f, indent=2)

        return jsonify({
            'message': 'Recommendations generated successfully',
            'output_file': output_filename
        })

    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON file. Please upload a valid JSON file.'}), 400
    except Exception as e:
        logger.exception(f"Error in upload_json: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the data. Please check the server logs for more information.'}), 500




    

if __name__ == '__main__':
    app.run(debug=False,port="5003")
