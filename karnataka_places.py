"""
Karnataka Places & Boundary Verification Engine
===============================================
Authoritative location lookup, boundary validation, and coordinate resolver
utilizing the 30,753-row Karnataka Local Government Directory (LGD) dataset
(karnataka_villages.csv) and comprehensive Indian administrative geographical boundaries.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
import pandas as pd

from config import PROCESSED_DIR, BASE_DIR

# -----------------------------------------------------------------------------
# 1. OUTSIDE KARNATAKA REFERENCE DICTIONARY (All other Indian States/UTs & Cities)
# -----------------------------------------------------------------------------
OUTSIDE_KARNATAKA_LOCATIONS = {
    # All 28 States & 8 UTs of India (excluding Karnataka)
    "goa": {"lat": 15.2993, "lon": 74.1240, "name": "Goa, India", "admin1": "Goa", "country": "India"},
    "sikkim": {"lat": 27.5330, "lon": 88.5122, "name": "Sikkim, India", "admin1": "Sikkim", "country": "India"},
    "andhra pradesh": {"lat": 15.9129, "lon": 79.7400, "name": "Andhra Pradesh, India", "admin1": "Andhra Pradesh", "country": "India"},
    "andhra": {"lat": 15.9129, "lon": 79.7400, "name": "Andhra Pradesh, India", "admin1": "Andhra Pradesh", "country": "India"},
    "kerala": {"lat": 10.8505, "lon": 76.2711, "name": "Kerala, India", "admin1": "Kerala", "country": "India"},
    "tamil nadu": {"lat": 11.1271, "lon": 78.6569, "name": "Tamil Nadu, India", "admin1": "Tamil Nadu", "country": "India"},
    "tamilnadu": {"lat": 11.1271, "lon": 78.6569, "name": "Tamil Nadu, India", "admin1": "Tamil Nadu", "country": "India"},
    "maharashtra": {"lat": 19.7515, "lon": 75.7139, "name": "Maharashtra, India", "admin1": "Maharashtra", "country": "India"},
    "telangana": {"lat": 18.1124, "lon": 79.0193, "name": "Telangana, India", "admin1": "Telangana", "country": "India"},
    "delhi": {"lat": 28.6139, "lon": 77.2090, "name": "Delhi, India", "admin1": "Delhi", "country": "India"},
    "new delhi": {"lat": 28.6139, "lon": 77.2090, "name": "New Delhi, India", "admin1": "Delhi", "country": "India"},
    "gujarat": {"lat": 22.2587, "lon": 71.1924, "name": "Gujarat, India", "admin1": "Gujarat", "country": "India"},
    "rajasthan": {"lat": 27.0238, "lon": 74.2179, "name": "Rajasthan, India", "admin1": "Rajasthan", "country": "India"},
    "punjab": {"lat": 31.1471, "lon": 75.3412, "name": "Punjab, India", "admin1": "Punjab", "country": "India"},
    "haryana": {"lat": 29.0588, "lon": 76.0856, "name": "Haryana, India", "admin1": "Haryana", "country": "India"},
    "uttar pradesh": {"lat": 26.8467, "lon": 80.9462, "name": "Uttar Pradesh, India", "admin1": "Uttar Pradesh", "country": "India"},
    "madhya pradesh": {"lat": 22.9734, "lon": 78.6569, "name": "Madhya Pradesh, India", "admin1": "Madhya Pradesh", "country": "India"},
    "west bengal": {"lat": 22.9868, "lon": 87.8550, "name": "West Bengal, India", "admin1": "West Bengal", "country": "India"},
    "bihar": {"lat": 25.0961, "lon": 85.3131, "name": "Bihar, India", "admin1": "Bihar", "country": "India"},
    "odisha": {"lat": 20.9517, "lon": 85.0985, "name": "Odisha, India", "admin1": "Odisha", "country": "India"},
    "orissa": {"lat": 20.9517, "lon": 85.0985, "name": "Odisha, India", "admin1": "Odisha", "country": "India"},
    "assam": {"lat": 26.2006, "lon": 92.9376, "name": "Assam, India", "admin1": "Assam", "country": "India"},
    "himachal pradesh": {"lat": 31.1048, "lon": 77.1734, "name": "Himachal Pradesh, India", "admin1": "Himachal Pradesh", "country": "India"},
    "jammu and kashmir": {"lat": 33.7782, "lon": 76.5762, "name": "Jammu and Kashmir, India", "admin1": "Jammu and Kashmir", "country": "India"},
    "kashmir": {"lat": 33.7782, "lon": 76.5762, "name": "Jammu and Kashmir, India", "admin1": "Jammu and Kashmir", "country": "India"},
    "ladakh": {"lat": 34.1526, "lon": 77.5771, "name": "Ladakh, India", "admin1": "Ladakh", "country": "India"},
    "uttarakhand": {"lat": 30.0668, "lon": 79.0193, "name": "Uttarakhand, India", "admin1": "Uttarakhand", "country": "India"},
    "chhattisgarh": {"lat": 21.2787, "lon": 81.8661, "name": "Chhattisgarh, India", "admin1": "Chhattisgarh", "country": "India"},
    "jharkhand": {"lat": 23.6102, "lon": 85.2799, "name": "Jharkhand, India", "admin1": "Jharkhand", "country": "India"},
    "tripura": {"lat": 23.9408, "lon": 91.9882, "name": "Tripura, India", "admin1": "Tripura", "country": "India"},
    "manipur": {"lat": 24.6637, "lon": 93.9063, "name": "Manipur, India", "admin1": "Manipur", "country": "India"},
    "meghalaya": {"lat": 25.4670, "lon": 91.3662, "name": "Meghalaya, India", "admin1": "Meghalaya", "country": "India"},
    "nagaland": {"lat": 26.1584, "lon": 94.5624, "name": "Nagaland, India", "admin1": "Nagaland", "country": "India"},
    "mizoram": {"lat": 23.1645, "lon": 92.9376, "name": "Mizoram, India", "admin1": "Mizoram", "country": "India"},
    "arunachal pradesh": {"lat": 28.2180, "lon": 94.7278, "name": "Arunachal Pradesh, India", "admin1": "Arunachal Pradesh", "country": "India"},
    "puducherry": {"lat": 11.9416, "lon": 79.8083, "name": "Puducherry, India", "admin1": "Puducherry", "country": "India"},
    "pondicherry": {"lat": 11.9416, "lon": 79.8083, "name": "Puducherry, India", "admin1": "Puducherry", "country": "India"},
    "chandigarh": {"lat": 30.7333, "lon": 76.7794, "name": "Chandigarh, India", "admin1": "Chandigarh", "country": "India"},

    # Major Indian & World Cities Outside Karnataka
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai, Maharashtra, India", "admin1": "Maharashtra", "country": "India"},
    "bombay": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai, Maharashtra, India", "admin1": "Maharashtra", "country": "India"},
    "pune": {"lat": 18.5204, "lon": 73.8567, "name": "Pune, Maharashtra, India", "admin1": "Maharashtra", "country": "India"},
    "panaji": {"lat": 15.4909, "lon": 73.8278, "name": "Panaji, Goa, India", "admin1": "Goa", "country": "India"},
    "margao": {"lat": 15.2832, "lon": 73.9862, "name": "Margao, Goa, India", "admin1": "Goa", "country": "India"},
    "vasco": {"lat": 15.3982, "lon": 73.8113, "name": "Vasco da Gama, Goa, India", "admin1": "Goa", "country": "India"},
    "mapusa": {"lat": 15.5937, "lon": 73.8142, "name": "Mapusa, Goa, India", "admin1": "Goa", "country": "India"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "name": "Chennai, Tamil Nadu, India", "admin1": "Tamil Nadu", "country": "India"},
    "madras": {"lat": 13.0827, "lon": 80.2707, "name": "Chennai, Tamil Nadu, India", "admin1": "Tamil Nadu", "country": "India"},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "name": "Hyderabad, Telangana, India", "admin1": "Telangana", "country": "India"},
    "secunderabad": {"lat": 17.4399, "lon": 78.4983, "name": "Secunderabad, Telangana, India", "admin1": "Telangana", "country": "India"},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "name": "Kolkata, West Bengal, India", "admin1": "West Bengal", "country": "India"},
    "calcutta": {"lat": 22.5726, "lon": 88.3639, "name": "Kolkata, West Bengal, India", "admin1": "West Bengal", "country": "India"},
    "kochi": {"lat": 9.9312, "lon": 76.2673, "name": "Kochi, Kerala, India", "admin1": "Kerala", "country": "India"},
    "cochin": {"lat": 9.9312, "lon": 76.2673, "name": "Kochi, Kerala, India", "admin1": "Kerala", "country": "India"},
    "thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366, "name": "Thiruvananthapuram, Kerala, India", "admin1": "Kerala", "country": "India"},
    "trivandrum": {"lat": 8.5241, "lon": 76.9366, "name": "Thiruvananthapuram, Kerala, India", "admin1": "Kerala", "country": "India"},
    "kozhikode": {"lat": 11.2588, "lon": 75.7804, "name": "Kozhikode, Kerala, India", "admin1": "Kerala", "country": "India"},
    "calicut": {"lat": 11.2588, "lon": 75.7804, "name": "Kozhikode, Kerala, India", "admin1": "Kerala", "country": "India"},
    "kannur": {"lat": 11.8745, "lon": 75.3704, "name": "Kannur, Kerala, India", "admin1": "Kerala", "country": "India"},
    "kasaragod": {"lat": 12.5102, "lon": 74.9852, "name": "Kasaragod, Kerala, India", "admin1": "Kerala", "country": "India"},
    "gangtok": {"lat": 27.3389, "lon": 88.6065, "name": "Gangtok, Sikkim, India", "admin1": "Sikkim", "country": "India"},
    "visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "name": "Visakhapatnam, Andhra Pradesh, India", "admin1": "Andhra Pradesh", "country": "India"},
    "vizag": {"lat": 17.6868, "lon": 83.2185, "name": "Visakhapatnam, Andhra Pradesh, India", "admin1": "Andhra Pradesh", "country": "India"},
    "vijayawada": {"lat": 16.5062, "lon": 80.6480, "name": "Vijayawada, Andhra Pradesh, India", "admin1": "Andhra Pradesh", "country": "India"},
    "tirupati": {"lat": 13.6288, "lon": 79.4192, "name": "Tirupati, Andhra Pradesh, India", "admin1": "Andhra Pradesh", "country": "India"},
    "jaipur": {"lat": 26.9124, "lon": 75.7873, "name": "Jaipur, Rajasthan, India", "admin1": "Rajasthan", "country": "India"},
    "lucknow": {"lat": 26.8467, "lon": 80.9462, "name": "Lucknow, Uttar Pradesh, India", "admin1": "Uttar Pradesh", "country": "India"},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714, "name": "Ahmedabad, Gujarat, India", "admin1": "Gujarat", "country": "India"},
    "patna": {"lat": 25.5941, "lon": 85.1376, "name": "Patna, Bihar, India", "admin1": "Bihar", "country": "India"},
    "bhopal": {"lat": 23.2599, "lon": 77.4126, "name": "Bhopal, Madhya Pradesh, India", "admin1": "Madhya Pradesh", "country": "India"},
    "guwahati": {"lat": 26.1445, "lon": 91.7362, "name": "Guwahati, Assam, India", "admin1": "Assam", "country": "India"},
    "london": {"lat": 51.5074, "lon": -0.1278, "name": "London, United Kingdom", "admin1": "England", "country": "United Kingdom"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York, United States", "admin1": "New York", "country": "United States"},
    "dubai": {"lat": 25.2048, "lon": 55.2708, "name": "Dubai, United Arab Emirates", "admin1": "Dubai", "country": "United Arab Emirates"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "name": "Singapore", "admin1": "Singapore", "country": "Singapore"},
}


# -----------------------------------------------------------------------------
# 2. ALL 31 KARNATAKA DISTRICT HEADQUARTERS & MAJOR CITIES
# -----------------------------------------------------------------------------
KARNATAKA_DISTRICT_CENTERS = {
    "bagalkote": {"lat": 16.1875, "lon": 75.6980, "name": "Bagalkote, Karnataka, India", "admin1": "Karnataka", "district": "Bagalkote"},
    "ballari": {"lat": 15.1394, "lon": 76.9214, "name": "Ballari (Bellary), Karnataka, India", "admin1": "Karnataka", "district": "Ballari"},
    "bellary": {"lat": 15.1394, "lon": 76.9214, "name": "Ballari (Bellary), Karnataka, India", "admin1": "Karnataka", "district": "Ballari"},
    "belagavi": {"lat": 15.8497, "lon": 74.4977, "name": "Belagavi (Belgaum), Karnataka, India", "admin1": "Karnataka", "district": "Belagavi"},
    "belgaum": {"lat": 15.8497, "lon": 74.4977, "name": "Belagavi (Belgaum), Karnataka, India", "admin1": "Karnataka", "district": "Belagavi"},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946, "name": "Bengaluru (Bangalore), Karnataka, India", "admin1": "Karnataka", "district": "Bengaluru Urban"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "name": "Bengaluru (Bangalore), Karnataka, India", "admin1": "Karnataka", "district": "Bengaluru Urban"},
    "bengaluru rural": {"lat": 13.2323, "lon": 77.5684, "name": "Bengaluru Rural, Karnataka, India", "admin1": "Karnataka", "district": "Bengaluru Rural"},
    "bengaluru urban": {"lat": 12.9716, "lon": 77.5946, "name": "Bengaluru Urban, Karnataka, India", "admin1": "Karnataka", "district": "Bengaluru Urban"},
    "bidar": {"lat": 17.9104, "lon": 77.5199, "name": "Bidar, Karnataka, India", "admin1": "Karnataka", "district": "Bidar"},
    "chamarajanagar": {"lat": 11.9261, "lon": 76.9437, "name": "Chamarajanagar, Karnataka, India", "admin1": "Karnataka", "district": "Chamarajanagar"},
    "chikkaballapura": {"lat": 13.4325, "lon": 77.7275, "name": "Chikkaballapura, Karnataka, India", "admin1": "Karnataka", "district": "Chikkaballapura"},
    "chikkamagaluru": {"lat": 13.3161, "lon": 75.7720, "name": "Chikkamagaluru (Chikmagalur), Karnataka, India", "admin1": "Karnataka", "district": "Chikkamagaluru"},
    "chikmagalur": {"lat": 13.3161, "lon": 75.7720, "name": "Chikkamagaluru (Chikmagalur), Karnataka, India", "admin1": "Karnataka", "district": "Chikkamagaluru"},
    "chitradurga": {"lat": 14.2251, "lon": 76.3980, "name": "Chitradurga, Karnataka, India", "admin1": "Karnataka", "district": "Chitradurga"},
    "dakshina kannada": {"lat": 12.9141, "lon": 74.8560, "name": "Dakshina Kannada (Mangaluru), Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "davanagere": {"lat": 14.4644, "lon": 75.9218, "name": "Davanagere, Karnataka, India", "admin1": "Karnataka", "district": "Davanagere"},
    "dharwad": {"lat": 15.4589, "lon": 75.0078, "name": "Dharwad, Karnataka, India", "admin1": "Karnataka", "district": "Dharwad"},
    "hubli": {"lat": 15.3647, "lon": 75.1240, "name": "Hubballi (Hubli), Karnataka, India", "admin1": "Karnataka", "district": "Dharwad"},
    "hubballi": {"lat": 15.3647, "lon": 75.1240, "name": "Hubballi (Hubli), Karnataka, India", "admin1": "Karnataka", "district": "Dharwad"},
    "gadag": {"lat": 15.4167, "lon": 75.6333, "name": "Gadag, Karnataka, India", "admin1": "Karnataka", "district": "Gadag"},
    "hassan": {"lat": 13.0033, "lon": 76.1004, "name": "Hassan, Karnataka, India", "admin1": "Karnataka", "district": "Hassan"},
    "haveri": {"lat": 14.7950, "lon": 75.3990, "name": "Haveri, Karnataka, India", "admin1": "Karnataka", "district": "Haveri"},
    "kalaburagi": {"lat": 17.3297, "lon": 76.8343, "name": "Kalaburagi (Gulbarga), Karnataka, India", "admin1": "Karnataka", "district": "Kalaburagi"},
    "gulbarga": {"lat": 17.3297, "lon": 76.8343, "name": "Kalaburagi (Gulbarga), Karnataka, India", "admin1": "Karnataka", "district": "Kalaburagi"},
    "kodagu": {"lat": 12.4244, "lon": 75.7382, "name": "Madikeri (Kodagu/Coorg), Karnataka, India", "admin1": "Karnataka", "district": "Kodagu"},
    "coorg": {"lat": 12.4244, "lon": 75.7382, "name": "Madikeri (Kodagu/Coorg), Karnataka, India", "admin1": "Karnataka", "district": "Kodagu"},
    "madikeri": {"lat": 12.4244, "lon": 75.7382, "name": "Madikeri, Kodagu, Karnataka, India", "admin1": "Karnataka", "district": "Kodagu"},
    "kolar": {"lat": 13.1367, "lon": 78.1292, "name": "Kolar, Karnataka, India", "admin1": "Karnataka", "district": "Kolar"},
    "koppal": {"lat": 15.3456, "lon": 76.1554, "name": "Koppal, Karnataka, India", "admin1": "Karnataka", "district": "Koppal"},
    "mandya": {"lat": 12.5218, "lon": 76.8951, "name": "Mandya, Karnataka, India", "admin1": "Karnataka", "district": "Mandya"},
    "mysuru": {"lat": 12.2958, "lon": 76.6394, "name": "Mysuru (Mysore), Karnataka, India", "admin1": "Karnataka", "district": "Mysuru"},
    "mysore": {"lat": 12.2958, "lon": 76.6394, "name": "Mysuru (Mysore), Karnataka, India", "admin1": "Karnataka", "district": "Mysuru"},
    "raichur": {"lat": 16.2120, "lon": 77.3439, "name": "Raichur, Karnataka, India", "admin1": "Karnataka", "district": "Raichur"},
    "shivamogga": {"lat": 13.9299, "lon": 75.5681, "name": "Shivamogga (Shimoga), Karnataka, India", "admin1": "Karnataka", "district": "Shivamogga"},
    "shimoga": {"lat": 13.9299, "lon": 75.5681, "name": "Shivamogga (Shimoga), Karnataka, India", "admin1": "Karnataka", "district": "Shivamogga"},
    "tumakuru": {"lat": 13.3409, "lon": 77.1010, "name": "Tumakuru (Tumkur), Karnataka, India", "admin1": "Karnataka", "district": "Tumakuru"},
    "tumkur": {"lat": 13.3409, "lon": 77.1010, "name": "Tumakuru (Tumkur), Karnataka, India", "admin1": "Karnataka", "district": "Tumakuru"},
    "udupi": {"lat": 13.3409, "lon": 74.7421, "name": "Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "uttara kannada": {"lat": 14.8094, "lon": 74.1303, "name": "Karwar (Uttara Kannada), Karnataka, India", "admin1": "Karnataka", "district": "Uttara Kannada"},
    "karwar": {"lat": 14.8094, "lon": 74.1303, "name": "Karwar, Uttara Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Uttara Kannada"},
    "vijayanagara": {"lat": 15.2689, "lon": 76.3909, "name": "Hosapete (Vijayanagara), Karnataka, India", "admin1": "Karnataka", "district": "Vijayanagara"},
    "hosapete": {"lat": 15.2689, "lon": 76.3909, "name": "Hosapete (Hospet), Vijayanagara, Karnataka, India", "admin1": "Karnataka", "district": "Vijayanagara"},
    "hospet": {"lat": 15.2689, "lon": 76.3909, "name": "Hosapete (Hospet), Vijayanagara, Karnataka, India", "admin1": "Karnataka", "district": "Vijayanagara"},
    "vijayapura": {"lat": 16.8302, "lon": 75.7100, "name": "Vijayapura (Bijapur), Karnataka, India", "admin1": "Karnataka", "district": "Vijayapura"},
    "bijapur": {"lat": 16.8302, "lon": 75.7100, "name": "Vijayapura (Bijapur), Karnataka, India", "admin1": "Karnataka", "district": "Vijayapura"},
    "yadgir": {"lat": 16.7644, "lon": 77.1378, "name": "Yadgir, Karnataka, India", "admin1": "Karnataka", "district": "Yadgir"},

    # Coastal & Malenadu Taluk Centers (High Convective Zone)
    "mangaluru": {"lat": 12.9141, "lon": 74.8560, "name": "Mangaluru (Mangalore), Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "mangalore": {"lat": 12.9141, "lon": 74.8560, "name": "Mangaluru (Mangalore), Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "puttur": {"lat": 12.7667, "lon": 75.2016, "name": "Puttur, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "bantwal": {"lat": 12.8900, "lon": 75.0300, "name": "Bantwal, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "sullia": {"lat": 12.5606, "lon": 75.3905, "name": "Sullia, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "belthangady": {"lat": 12.9961, "lon": 75.2570, "name": "Belthangady, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "kadaba": {"lat": 12.7482, "lon": 75.4419, "name": "Kadaba, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "moodbidri": {"lat": 13.0699, "lon": 74.9961, "name": "Moodbidri, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "mulki": {"lat": 13.0900, "lon": 74.7900, "name": "Mulki, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "vitla": {"lat": 12.7674, "lon": 75.1012, "name": "Vitla, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "vittla": {"lat": 12.7674, "lon": 75.1012, "name": "Vitla, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "uppinangady": {"lat": 12.8420, "lon": 75.2950, "name": "Uppinangady, Dakshina Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Dakshina Kannada"},
    "kundapura": {"lat": 13.6268, "lon": 74.6917, "name": "Kundapura, Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "karkala": {"lat": 13.2140, "lon": 74.9972, "name": "Karkala, Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "byndoor": {"lat": 13.8741, "lon": 74.6300, "name": "Byndoor, Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "brahmavara": {"lat": 13.4277, "lon": 74.7466, "name": "Brahmavara, Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "kapu": {"lat": 13.2248, "lon": 74.7431, "name": "Kapu (Kaup), Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "kaup": {"lat": 13.2248, "lon": 74.7431, "name": "Kapu (Kaup), Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "hebri": {"lat": 13.3283, "lon": 74.9917, "name": "Hebri, Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "manipal": {"lat": 13.3525, "lon": 74.7869, "name": "Manipal, Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "malpe": {"lat": 13.3582, "lon": 74.7042, "name": "Malpe, Udupi, Karnataka, India", "admin1": "Karnataka", "district": "Udupi"},
    "somvarpet": {"lat": 12.5978, "lon": 75.8569, "name": "Somwarpet, Kodagu, Karnataka, India", "admin1": "Karnataka", "district": "Kodagu"},
    "virajpet": {"lat": 12.1983, "lon": 75.8078, "name": "Virajpet, Kodagu, Karnataka, India", "admin1": "Karnataka", "district": "Kodagu"},
    "kushalnagar": {"lat": 12.4565, "lon": 75.9642, "name": "Kushalnagar, Kodagu, Karnataka, India", "admin1": "Karnataka", "district": "Kodagu"},
    "gonikoppal": {"lat": 12.1818, "lon": 75.8943, "name": "Gonikoppal, Kodagu, Karnataka, India", "admin1": "Karnataka", "district": "Kodagu"},
    "bhadravathi": {"lat": 13.8413, "lon": 75.7032, "name": "Bhadravathi, Shivamogga, Karnataka, India", "admin1": "Karnataka", "district": "Shivamogga"},
    "gokarna": {"lat": 14.5435, "lon": 74.3188, "name": "Gokarna, Uttara Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Uttara Kannada"},
    "sirsi": {"lat": 14.6195, "lon": 74.8354, "name": "Sirsi, Uttara Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Uttara Kannada"},
    "dandeli": {"lat": 15.2361, "lon": 74.6173, "name": "Dandeli, Uttara Kannada, Karnataka, India", "admin1": "Karnataka", "district": "Uttara Kannada"},
    "mudigere": {"lat": 13.1364, "lon": 75.6385, "name": "Mudigere, Chikkamagaluru, Karnataka, India", "admin1": "Karnataka", "district": "Chikkamagaluru"},
    "tarikere": {"lat": 13.7133, "lon": 75.8167, "name": "Tarikere, Chikkamagaluru, Karnataka, India", "admin1": "Karnataka", "district": "Chikkamagaluru"},
    "sandur": {"lat": 15.0883, "lon": 76.5478, "name": "Sandur, Ballari, Karnataka, India", "admin1": "Karnataka", "district": "Ballari"},
    "gokak": {"lat": 16.1667, "lon": 74.8333, "name": "Gokak, Belagavi, Karnataka, India", "admin1": "Karnataka", "district": "Belagavi"},
    "channapatna": {"lat": 12.6517, "lon": 77.2089, "name": "Channapatna, Ramanagara, Karnataka, India", "admin1": "Karnataka", "district": "Ramanagara"},
    "tiptur": {"lat": 13.2556, "lon": 76.4789, "name": "Tiptur, Tumakuru, Karnataka, India", "admin1": "Karnataka", "district": "Tumakuru"},
}


# -----------------------------------------------------------------------------
# 3. LOAD & INDEX 30,753 KARNATAKA VILLAGES DATASET
# -----------------------------------------------------------------------------
_VILLAGES_CSV_PATH = PROCESSED_DIR / "karnataka_villages.csv"

_KARNATAKA_DISTRICTS = set()
_KARNATAKA_MANDALS = set()
_VILLAGE_LOOKUP = {}  # cleaned_name -> {village, mandal, district, pincode}

def _clean_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    # remove leading numbers, e.g. "102 Nekkilady" -> "nekkilady"
    cleaned = re.sub(r"^\d+(\w+)?\s*(-|\s)?\s*", "", s.lower().strip())
    # remove parenthetical suffixes like "(ct)"
    cleaned = re.sub(r"\s*\([^)]*\)", "", cleaned).strip()
    return cleaned

def _init_places_database():
    global _KARNATAKA_DISTRICTS, _KARNATAKA_MANDALS, _VILLAGE_LOOKUP
    if _KARNATAKA_DISTRICTS:
        return  # already initialized

    if not _VILLAGES_CSV_PATH.exists():
        print(f"[WARNING] karnataka_villages.csv not found at: {_VILLAGES_CSV_PATH}")
        return

    try:
        df = pd.read_csv(_VILLAGES_CSV_PATH, low_memory=False)
        _KARNATAKA_DISTRICTS = set(df['District'].dropna().str.lower().str.strip().unique())
        _KARNATAKA_MANDALS = set(df['Mandal'].dropna().str.lower().str.strip().unique())

        for _, row in df.iterrows():
            v_raw = str(row.get('Village', '')).strip()
            v_clean = _clean_text(v_raw)
            m_name = str(row.get('Mandal', '')).strip()
            d_name = str(row.get('District', '')).strip()
            pin = str(row.get('Pincode', '')).replace('.0', '').strip()

            meta = {
                "village": v_raw,
                "clean_name": v_clean,
                "mandal": m_name,
                "district": d_name,
                "pincode": pin
            }

            if v_clean and v_clean not in _VILLAGE_LOOKUP:
                _VILLAGE_LOOKUP[v_clean] = meta
            v_raw_lower = v_raw.lower()
            if v_raw_lower not in _VILLAGE_LOOKUP:
                _VILLAGE_LOOKUP[v_raw_lower] = meta

        print(f"[AeroCast Places] Successfully indexed {len(df):,} Karnataka villages, {len(_KARNATAKA_MANDALS)} mandals, and {len(_KARNATAKA_DISTRICTS)} districts.")
    except Exception as e:
        print(f"[ERROR] Failed to index karnataka_villages.csv: {e}")

# Initialize on module import
_init_places_database()


# -----------------------------------------------------------------------------
# 4. LOCATION VERIFICATION & COORDINATE RESOLUTION
# -----------------------------------------------------------------------------
def is_lat_lon_in_karnataka(lat: float, lon: float) -> bool:
    """Strictly verify if latitude and longitude fall within Karnataka's geographical bounds."""
    # Karnataka bounding box: 11.5°N - 18.6°N, 74.0°E - 78.6°E
    return (11.45 <= lat <= 18.65) and (74.00 <= lon <= 78.65)


def is_explicitly_outside_karnataka(location: str) -> tuple[bool, dict | None]:
    """Check if location query is an Indian state outside Karnataka or known non-KA city."""
    loc_clean = location.lower().strip()

    # Exact match in outside locations reference
    if loc_clean in OUTSIDE_KARNATAKA_LOCATIONS:
        info = dict(OUTSIDE_KARNATAKA_LOCATIONS[loc_clean])
        info["is_karnataka"] = False
        return (True, info)

    # Word-boundary check against outside states and major cities
    for outside_key, info in OUTSIDE_KARNATAKA_LOCATIONS.items():
        pattern = r"\b" + re.escape(outside_key) + r"\b"
        if re.search(pattern, loc_clean):
            # Double-check it doesn't also contain "karnataka"
            if "karnataka" not in loc_clean:
                res = dict(info)
                res["is_karnataka"] = False
                return (True, res)

    return (False, None)


def lookup_karnataka_place_metadata(location: str) -> dict | None:
    """Lookup if query matches a known Karnataka district, mandal, or village."""
    loc_clean = _clean_text(location)
    raw_lower = location.lower().strip()

    # Check city coordinates dictionary first
    if raw_lower in KARNATAKA_DISTRICT_CENTERS:
        res = dict(KARNATAKA_DISTRICT_CENTERS[raw_lower])
        res["is_karnataka"] = True
        return res

    # Check village lookup
    if loc_clean in _VILLAGE_LOOKUP:
        return _VILLAGE_LOOKUP[loc_clean]
    if raw_lower in _VILLAGE_LOOKUP:
        return _VILLAGE_LOOKUP[raw_lower]

    # Check mandals (taluks)
    if loc_clean in _KARNATAKA_MANDALS or raw_lower in _KARNATAKA_MANDALS:
        return {"mandal": location.title(), "district": "Karnataka", "is_karnataka": True}

    # Check districts
    if loc_clean in _KARNATAKA_DISTRICTS or raw_lower in _KARNATAKA_DISTRICTS:
        return {"district": location.title(), "is_karnataka": True}

    return None


def resolve_pinpoint_coordinates(location: str) -> dict:
    """
    Master Coordinate & State-Boundary Resolver:
    1. Detects places outside Karnataka (Goa, Sikkim, Andhra Pradesh, etc.) -> returns REAL coordinates, is_karnataka=False.
    2. Detects Karnataka districts/taluks/villages -> returns accurate coordinates, is_karnataka=True.
    3. Dynamically geocodes and strictly checks bounds.
    """
    loc_clean = location.strip()
    loc_lower = loc_clean.lower()

    # 1. IMMEDIATE REJECTION of outside Indian States & non-Karnataka locations
    is_outside, outside_info = is_explicitly_outside_karnataka(loc_lower)
    if is_outside and outside_info:
        return outside_info

    # 2. Check predefined Karnataka District & Taluk centers
    if loc_lower in KARNATAKA_DISTRICT_CENTERS:
        res = dict(KARNATAKA_DISTRICT_CENTERS[loc_lower])
        res["is_karnataka"] = True
        return res

    for k, info in KARNATAKA_DISTRICT_CENTERS.items():
        if k == loc_lower or (len(loc_lower) >= 4 and (k in loc_lower or loc_lower in k)):
            res = dict(info)
            res["is_karnataka"] = True
            return res

    # 3. Check Village / Mandal from karnataka_villages.csv
    v_meta = lookup_karnataka_place_metadata(loc_lower)
    search_query = loc_clean
    if v_meta and "mandal" in v_meta and "district" in v_meta:
        search_query = f"{v_meta.get('village', loc_clean)}, {v_meta['mandal']}, {v_meta['district']}, Karnataka, India"

    # 4. Dynamic Geocoding via Open-Meteo
    headers = {'User-Agent': 'AeroCast/2.0 (Karnataka Convective Weather Nowcasting)'}
    gurl = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(search_query)}&count=5&language=en&format=json"

    try:
        greq = urllib.request.Request(gurl, headers=headers)
        gresp = urllib.request.urlopen(greq, timeout=6)
        gdata = json.loads(gresp.read().decode('utf-8'))
        results = gdata.get('results', [])

        if results:
            # First preference: Find result that is specifically in Karnataka, India
            for r in results:
                country = r.get('country', '')
                admin1 = r.get('admin1', '')
                lat = float(r['latitude'])
                lon = float(r['longitude'])

                if country.lower() == 'india' and admin1.lower() == 'karnataka' and is_lat_lon_in_karnataka(lat, lon):
                    return {
                        "lat": lat,
                        "lon": lon,
                        "name": f"{r.get('name')}, {admin1}, India",
                        "is_karnataka": True,
                        "country": "India",
                        "admin1": "Karnataka"
                    }

            # Top result (Outside Karnataka)
            top = results[0]
            top_lat = float(top['latitude'])
            top_lon = float(top['longitude'])
            top_country = top.get('country', 'Unknown')
            top_admin1 = top.get('admin1', '')

            # Verify if top result is actually inside Karnataka boundary
            is_ka = (top_country.lower() == 'india' and 
                     top_admin1.lower() == 'karnataka' and 
                     is_lat_lon_in_karnataka(top_lat, top_lon))

            return {
                "lat": top_lat,
                "lon": top_lon,
                "name": f"{top.get('name')}, {top_admin1 + ', ' if top_admin1 else ''}{top_country}",
                "is_karnataka": is_ka,
                "country": top_country,
                "admin1": top_admin1
            }
    except Exception as e:
        print(f"[WARNING] Geocoding exception for '{location}': {e}")

    # Fallback: If place was verified in karnataka_villages.csv, use its Mandal or District coordinates
    if v_meta and (v_meta.get("is_karnataka") or "mandal" in v_meta or "district" in v_meta):
        m_key = str(v_meta.get("mandal", "")).lower().strip()
        d_key = str(v_meta.get("district", "")).lower().strip()
        
        m_coord = KARNATAKA_DISTRICT_CENTERS.get(m_key)
        d_coord = KARNATAKA_DISTRICT_CENTERS.get(d_key)
        ref_coord = m_coord or d_coord or {"lat": 12.9141, "lon": 74.8560}

        v_display = v_meta.get('village', location.title())
        m_display = v_meta.get('mandal', 'Karnataka')
        d_display = v_meta.get('district', 'Karnataka')

        return {
            "lat": ref_coord["lat"],
            "lon": ref_coord["lon"],
            "name": f"{v_display}, {m_display}, {d_display}, Karnataka, India",
            "is_karnataka": True,
            "country": "India",
            "admin1": "Karnataka"
        }

    # Ultimate fallback for completely unknown query: Outside Karnataka
    return {
        "lat": 20.5937,
        "lon": 78.9629,
        "name": f"{location.title()} (Location Outside Karnataka Grid)",
        "is_karnataka": False,
        "country": "Unknown",
        "admin1": "Unknown"
    }
