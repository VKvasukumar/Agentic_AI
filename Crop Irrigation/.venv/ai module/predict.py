import json
import random
import os

# Define realistic crop moisture thresholds
CROP_THRESHOLDS = {
    'Tomato': {'min_moisture': 40.0, 'target_moisture': 75.0, 'base_water_per_acre': 1200},
    'Paddy': {'min_moisture': 60.0, 'target_moisture': 90.0, 'base_water_per_acre': 2500},
    'Banana': {'min_moisture': 50.0, 'target_moisture': 80.0, 'base_water_per_acre': 2000},
    'Potato': {'min_moisture': 45.0, 'target_moisture': 70.0, 'base_water_per_acre': 1000},
    'Cotton': {'min_moisture': 35.0, 'target_moisture': 65.0, 'base_water_per_acre': 800}
}

# Define disease lists, descriptions, and treatments by crop
DISEASE_DATABASE = {
    'Tomato': [
        {
            'disease': 'Healthy',
            'health_status': 'Healthy',
            'confidence_range': (92.0, 98.0),
            'treatment': 'Continue regular watering and monitoring. Ensure good soil drainage and sunlight.',
            'recommendation': 'Maintain current schedule.'
        },
        {
            'disease': 'Early Blight',
            'health_status': 'Diseased',
            'confidence_range': (82.0, 92.0),
            'treatment': 'Apply copper-based fungicides. Prune lower leaves to improve air circulation. Avoid overhead watering.',
            'recommendation': 'Isolate affected plants; reduce humidity.'
        },
        {
            'disease': 'Late Blight',
            'health_status': 'Diseased',
            'confidence_range': (85.0, 94.0),
            'treatment': 'Remove and destroy infected plant debris immediately. Spray chlorothalonil or copper fungicides.',
            'recommendation': 'Urgent: Apply fungicide cover and trim leaves.'
        }
    ],
    'Banana': [
        {
            'disease': 'Healthy',
            'health_status': 'Healthy',
            'confidence_range': (90.0, 97.0),
            'treatment': 'Keep weeding the farm. Apply potassium-rich fertilizers to support strong stalk development.',
            'recommendation': 'Maintain standard fertilization and moisture.'
        },
        {
            'disease': 'Black Sigatoka',
            'health_status': 'Diseased',
            'confidence_range': (80.0, 90.0),
            'treatment': 'Deleaf infected leaves and burn them. Apply systemic fungicides in oil-water emulsions.',
            'recommendation': 'Prune affected leaves immediately to restrict spore spread.'
        },
        {
            'disease': 'Panama Disease',
            'health_status': 'Diseased',
            'confidence_range': (75.0, 88.0),
            'treatment': 'Soil-borne pathogen. No effective chemical treatment. Quarantine the infected area and plant resistant cultivars.',
            'recommendation': 'Strict quarantine; isolate soil beds.'
        }
    ],
    'Paddy': [
        {
            'disease': 'Healthy',
            'health_status': 'Healthy',
            'confidence_range': (93.0, 99.0),
            'treatment': 'Maintain standing water level of 2-5 cm. Apply balanced nitrogen doses.',
            'recommendation': 'Ensure stable flooding.'
        },
        {
            'disease': 'Blast Disease',
            'health_status': 'Diseased',
            'confidence_range': (83.0, 93.0),
            'treatment': 'Avoid excessive nitrogen. Spray tricyclazole or carbendazim at early infection stages.',
            'recommendation': 'Apply systemic fungicide; reduce nitrogen applications.'
        },
        {
            'disease': 'Brown Spot',
            'health_status': 'Diseased',
            'confidence_range': (80.0, 89.0),
            'treatment': 'Improve soil fertility, particularly potassium and silica. Apply Mancozeb or Edifenphos.',
            'recommendation': 'Optimize nutrient balance and spray fungicide.'
        }
    ],
    'Potato': [
        {
            'disease': 'Healthy',
            'health_status': 'Healthy',
            'confidence_range': (91.0, 96.0),
            'treatment': 'Hill potatoes regularly to protect tubers from sunlight. Practice crop rotation.',
            'recommendation': 'Normal cultivation.'
        },
        {
            'disease': 'Late Blight',
            'health_status': 'Diseased',
            'confidence_range': (86.0, 95.0),
            'treatment': 'Destructive disease. Spray metalaxyl-M or mancozeb. Destroy cull piles immediately.',
            'recommendation': 'High Alert: Apply chemical controls and monitor field moisture.'
        }
    ],
    'Cotton': [
        {
            'disease': 'Healthy',
            'health_status': 'Healthy',
            'confidence_range': (90.0, 98.0),
            'treatment': 'Ensure weed-free growth. Monitor for bollworm activity.',
            'recommendation': 'Standard monitoring.'
        },
        {
            'disease': 'Bacterial Blight',
            'health_status': 'Diseased',
            'confidence_range': (82.0, 91.0),
            'treatment': 'Use acid-delinted seeds. Spray copper oxychloride or streptomycin formulations.',
            'recommendation': 'Seed treatment and foliar copper sprays.'
        }
    ]
}

def predict_irrigation_recommendation(moisture, temperature, rainfall, forecast, crop_type, farm_size_acres=1.0):
    """
    Evaluates soil parameters and weather forecast to generate irrigation commands.
    """
    crop_info = CROP_THRESHOLDS.get(crop_type, CROP_THRESHOLDS['Tomato'])
    min_moist = crop_info['min_moisture']
    target_moist = crop_info['target_moisture']
    base_water = crop_info['base_water_per_acre']
    
    # Simple rule engine
    status = "No Irrigation Needed"
    water_volume = 0.0
    duration_mins = 0
    reason = "Soil moisture is optimal."
    confidence = 95.0
    
    # Adjust thresholds based on temperature
    # Higher temperature dries out soil faster, increasing threshold/need
    temp_factor = 1.0
    if temperature > 30.0:
        min_moist += 5.0
        temp_factor = 1.2
    elif temperature < 15.0:
        min_moist -= 3.0
        temp_factor = 0.8
        
    # Analyze need
    if moisture < min_moist:
        status = "Irrigation Recommended"
        deficit = target_moist - moisture
        
        # Calculate water volume (in Liters) based on deficit and size
        # 1 acre base needs base_water liters. Deficit adjusts the volume needed.
        water_volume = int(base_water * (deficit / 50.0) * temp_factor * farm_size_acres)
        
        # Assume pump rate of 50 Liters per minute
        duration_mins = max(5, int(water_volume / 50))
        
        # Factor in weather forecast
        if forecast == 'rainy':
            if rainfall > 10.0:
                status = "Delayed Irrigation"
                water_volume = 0.0
                duration_mins = 0
                reason = f"Soil moisture is low ({moisture:.1f}%), but heavy rain ({rainfall}mm) is forecast. Postponing irrigation."
                confidence = 88.0
            else:
                # Reduce irrigation due to light rain
                water_volume = int(water_volume * 0.5)
                duration_mins = max(5, int(water_volume / 50))
                reason = f"Soil moisture is low ({moisture:.1f}%). Light rain expected; irrigation reduced by 50%."
                confidence = 82.0
        else:
            reason = f"Soil moisture ({moisture:.1f}%) is below the critical threshold of {min_moist:.1f}% for {crop_type}."
            confidence = min(99.0, max(75.0, 100.0 - abs(moisture - min_moist)))
    else:
        # Moisture is okay, check if it's borderline and high heat is expected
        if moisture < (min_moist + 8.0) and temperature > 32.0 and forecast == 'sunny':
            status = "Pre-emptive Irrigation Recommended"
            water_volume = int(base_water * 0.4 * farm_size_acres)
            duration_mins = max(5, int(water_volume / 50))
            reason = f"Soil moisture ({moisture:.1f}%) is above minimum, but extreme heat ({temperature}°C) and sunny weather will deplete it rapidly."
            confidence = 80.0
        else:
            reason = f"Soil moisture ({moisture:.1f}%) is healthy for {crop_type} (minimum threshold: {min_moist:.1f}%)."
            confidence = min(99.0, max(85.0, 100.0 - (moisture - min_moist)))

    return {
        "status": status,
        "water_volume_liters": water_volume,
        "duration_minutes": duration_mins,
        "reason": reason,
        "confidence": round(confidence, 1)
    }

def predict_crop_disease(image_filename, crop_type):
    """
    Simulates disease detection logic based on uploaded images.
    Parses filename keywords (e.g. 'blight', 'spot') or defaults to crop database values.
    """
    if crop_type not in DISEASE_DATABASE:
        crop_type = 'Tomato'
        
    diseases = DISEASE_DATABASE[crop_type]
    
    # Try to extract from filename keywords to make upload demos feel interactive!
    filename_lower = image_filename.lower()
    
    matched_entry = None
    if 'healthy' in filename_lower or 'normal' in filename_lower:
        matched_entry = next((d for d in diseases if d['health_status'] == 'Healthy'), None)
    elif 'blight' in filename_lower:
        matched_entry = next((d for d in diseases if 'blight' in d['disease'].lower()), None)
    elif 'spot' in filename_lower:
        matched_entry = next((d for d in diseases if 'spot' in d['disease'].lower()), None)
    elif 'blast' in filename_lower:
        matched_entry = next((d for d in diseases if 'blast' in d['disease'].lower()), None)
    elif 'panama' in filename_lower:
        matched_entry = next((d for d in diseases if 'panama' in d['disease'].lower()), None)

    # Fallback: pick randomly if no filename matches
    if not matched_entry:
        # 40% healthy, 60% split between other diseases
        if random.random() < 0.4:
            matched_entry = next((d for d in diseases if d['health_status'] == 'Healthy'), diseases[0])
        else:
            diseased_list = [d for d in diseases if d['health_status'] == 'Diseased']
            if diseased_list:
                matched_entry = random.choice(diseased_list)
            else:
                matched_entry = diseases[0]

    confidence = round(random.uniform(matched_entry['confidence_range'][0], matched_entry['confidence_range'][1]), 1)
    
    return {
        "crop": crop_type,
        "health_status": matched_entry['health_status'],
        "disease": matched_entry['disease'],
        "confidence": confidence,
        "treatment": matched_entry['treatment'],
        "recommendation": matched_entry['recommendation']
    }
