import json
import datetime

class GasTurbine:
    def __init__(self, eoh_limit=32000, start_factor=15.0, nominal_efficiency=0.35, max_fouling_drop=0.05):
        """
        Initializes the Gas Turbine model with manufacturer parameters.
        :param eoh_limit: Equivalent Operating Hours limit for Major Overhaul (MO).
        :param start_factor: Hours added per start/stop cycle (f_s).
        :param nominal_efficiency: Base thermal efficiency (e.g., 35%).
        :param max_fouling_drop: Maximum acceptable drop in absolute efficiency due to fouling.
        """
        self.eoh_limit = eoh_limit
        self.start_factor = start_factor
        self.nominal_efficiency = nominal_efficiency
        self.max_fouling_drop = max_fouling_drop
        
    def calculate_eoh(self, oh, ns):
        """
        Calculates Equivalent Operating Hours (EOH).
        """
        return oh + (self.start_factor * ns)
        
    def calculate_fouling_indicator(self, current_efficiency):
        """
        Calculates Compressor Fouling Indicator based on efficiency drop.
        Returns the absolute drop in efficiency.
        """
        efficiency_drop = self.nominal_efficiency - current_efficiency
        return max(0.0, efficiency_drop)

    def calculate_thi(self, eoh, fouling_drop):
        """
        Computes the Turbine Health Index (THI) based on EOH and Fouling.
        Weights: 60% based on life consumption (EOH), 40% based on performance (Fouling).
        """
        # Life consumption health (0 to 100%)
        eoh_health = max(0.0, 100.0 * (1.0 - (eoh / self.eoh_limit)))
        
        # Performance health (0 to 100%)
        perf_health = max(0.0, 100.0 * (1.0 - (fouling_drop / self.max_fouling_drop)))
        
        # Weighted THI calculation
        thi = (0.6 * eoh_health) + (0.4 * perf_health)
        return max(0.0, min(100.0, thi))

    def evaluate_maintenance(self, current_oh, ns, current_efficiency):
        """
        Evaluates turbine health and generates maintenance recommendations.
        """
        eoh = self.calculate_eoh(current_oh, ns)
        fouling = self.calculate_fouling_indicator(current_efficiency)
        thi = self.calculate_thi(eoh, fouling)
        
        remaining_hours = max(0.0, self.eoh_limit - eoh)
        
        # Determine Maintenance Urgency
        urgency = "Normal Operation"
        action = "None"
        if thi < 60 or eoh >= self.eoh_limit:
            urgency = "Major Overhaul Required"
            action = "Schedule Major Overhaul (MO) immediately."
        elif 60 <= thi <= 80:
            urgency = "Minor Inspection / Combustion Inspection"
            action = "Schedule Boroscopic Inspection and Compressor Washing."
            
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "inputs": {
                "operating_hours": current_oh,
                "start_stop_cycles": ns,
                "current_efficiency": current_efficiency
            },
            "metrics": {
                "EOH": round(eoh, 2),
                "fouling_drop_absolute": round(fouling, 4),
                "THI_percentage": round(thi, 2),
                "remaining_eoh_to_mo": round(remaining_hours, 2)
            },
            "maintenance_recommendation": {
                "urgency_level": urgency,
                "recommended_action": action
            }
        }

def generate_cmms_work_order(evaluation_results, equipment_id, file_path="work_order.json"):
    """
    Simulates integration with a CMMS (SAP PM, Maximo) by exporting a structured JSON work order.
    """
    priority = "LOW"
    if evaluation_results["maintenance_recommendation"]["urgency_level"] == "Major Overhaul Required":
        priority = "HIGH"
    elif evaluation_results["maintenance_recommendation"]["urgency_level"] != "Normal Operation":
        priority = "MEDIUM"

    work_order = {
        "work_order_id": f"WO-{int(datetime.datetime.now().timestamp())}",
        "equipment_id": equipment_id,
        "priority": priority,
        "work_type": "PM",  # Preventive Maintenance
        "description": evaluation_results["maintenance_recommendation"]["recommended_action"],
        "health_index": evaluation_results["metrics"]["THI_percentage"],
        "trigger_conditions": {
            "EOH": evaluation_results["metrics"]["EOH"],
            "urgency": evaluation_results["maintenance_recommendation"]["urgency_level"]
        },
        "creation_date": evaluation_results["timestamp"]
    }
    
    with open(file_path, "w") as f:
        json.dump(work_order, f, indent=4)
        
    return work_order

if __name__ == "__main__":
    turbine = GasTurbine(eoh_limit=32000, start_factor=15.0, nominal_efficiency=0.35)
    
    print("=== CASE 1: HEALTHY TURBINE ===")
    healthy_eval = turbine.evaluate_maintenance(current_oh=12000, ns=100, current_efficiency=0.345)
    print(json.dumps(healthy_eval, indent=2))
    wo_healthy = generate_cmms_work_order(healthy_eval, equipment_id="GT-101", file_path="wo_healthy.json")
    print(f">> Work order exported for GT-101 (Priority: {wo_healthy['priority']})\n")
    
    print("=== CASE 2: HIGH DEGRADATION TURBINE ===")
    degraded_eval = turbine.evaluate_maintenance(current_oh=28000, ns=450, current_efficiency=0.31)
    print(json.dumps(degraded_eval, indent=2))
    wo_degraded = generate_cmms_work_order(degraded_eval, equipment_id="GT-102", file_path="wo_degraded.json")
    print(f">> Work order exported for GT-102 (Priority: {wo_degraded['priority']})\n")
