import json, random, math

def allocate_tokenized_load(current_load, energy_joules):
    """Adaptive GPU energy-token allocator."""
    stability = 1 - abs(math.sin(energy_joules / 1000))
    adjustment = random.uniform(-2, 2) * stability
    new_load = max(0, min(100, current_load + adjustment))
    token_value = (100 - new_load) / 100 * stability
    return {"target_load": new_load, "token": round(token_value, 4), "stability": round(stability, 3)}

if __name__ == "__main__":
    for i in range(5):
        print(json.dumps(allocate_tokenized_load(random.uniform(30,70), random.uniform(50,500)), indent=2))
