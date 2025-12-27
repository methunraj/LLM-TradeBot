with open('main.py', 'r') as f:
    content = f.read()

# Replace oi_fuel references with volume_fuel
content = content.replace("oi_fuel = sentiment.get('oi_fuel', {})", "volume_fuel = sentiment.get('volume_fuel', {})")
content = content.replace("oi_change = oi_fuel.get('oi_change_24h', 0)", "volume_surge = volume_fuel.get('volume_surge_pct', 0)")
content = content.replace("four_layer_result['oi_change'] = oi_change", "four_layer_result['volume_surge'] = volume_surge")

# Replace OI anomaly check with volume check
content = content.replace(
    "if abs(oi_change) > 200:",
    "# Volume surge anomaly check removed - no longer needed"
)
content = content.replace(
    'data_anomalies.append(f"OI_ANOMALY: {oi_change:.1f}% (>200% likely data error)")',
    '# OI anomaly check removed'
)
content = content.replace(
    'log.warning(f"⚠️ DATA ANOMALY: OI Change {oi_change:.1f}% is abnormally high")',
    ''
)
content = content.replace(
    "oi_change = max(min(oi_change, 100), -100)",
    "# No clamping needed for volume surge"
)
content = content.replace(
    "four_layer_result['oi_change_raw'] = oi_fuel.get('oi_change_24h', 0)",
    "four_layer_result['volume_surge_raw'] = volume_fuel.get('volume_surge_pct', 0)"
)

# Replace Layer 1 OI divergence checks with volume checks
content = content.replace(
    "elif trend_1h == 'long' and oi_change < -5.0:",
    "elif trend_1h == 'long' and volume_surge < -30:"
)
content = content.replace(
    'four_layer_result[\'blocking_reason\'] = f"OI Divergence: Trend UP but OI {oi_change:.1f}% (禁止开仓)"',
    'four_layer_result[\'blocking_reason\'] = f"Volume Divergence: Trend UP but volume {volume_surge:.1f}% (禁止开仓)"'
)
content = content.replace(
    'log.warning(f"🚨 Layer 1 FAIL: OI Divergence - Price up but OI {oi_change:.1f}%")',
    'log.warning(f"🚨 Layer 1 FAIL: Volume Divergence - Price up but volume {volume_surge:.1f}%")'
)

content = content.replace(
    "elif trend_1h == 'short' and oi_change > 5.0:",
    "elif trend_1h == 'short' and volume_surge > 50:"
)
content = content.replace(
    'four_layer_result[\'blocking_reason\'] = f"OI Divergence: Trend DOWN but OI +{oi_change:.1f}% (禁止开仓)"',
    'four_layer_result[\'blocking_reason\'] = f"Volume Divergence: Trend DOWN but volume +{volume_surge:.1f}% (禁止开仓)"'
)
content = content.replace(
    'log.warning(f"🚨 Layer 1 FAIL: OI Divergence - Price down but OI +{oi_change:.1f}%")',
    'log.warning(f"🚨 Layer 1 FAIL: Volume Divergence - Price down but volume +{volume_surge:.1f}%")'
)

# Replace weak fuel check
content = content.replace(
    "elif abs(oi_change) < 1.0:",
    "elif volume_surge < 20:"
)
content = content.replace(
    'four_layer_result[\'blocking_reason\'] = f"Weak Fuel (OI {oi_change:.1f}% < 1%)"',
    'four_layer_result[\'blocking_reason\'] = f"Weak Fuel (Volume surge {volume_surge:.1f}% < 20%)"'
)

# Replace whale trap check
content = content.replace(
    "elif trend_1h == 'long' and oi_fuel.get('whale_trap_risk', False):",
    "elif trend_1h == 'long' and volume_fuel.get('low_participation_risk', False):"
)
content = content.replace(
    'four_layer_result[\'blocking_reason\'] = f"Whale trap detected (OI {oi_change:.1f}%)"',
    'four_layer_result[\'blocking_reason\'] = f"Low participation risk (Volume {volume_surge:.1f}%)"'
)

# Replace fuel strength calculation
content = content.replace(
    "fuel_strength = 'Strong' if abs(oi_change) > 3.0 else 'Moderate'",
    "fuel_strength = 'Strong' if abs(volume_surge) > 50 else 'Moderate'"
)

with open('main.py', 'w') as f:
    f.write(content)

print("✅ Updated main.py Layer 1 logic to use volume surge")
