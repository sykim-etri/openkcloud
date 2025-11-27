#!/usr/bin/env python3
import sys
import os

# Add current path to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.gpu import ServerGpuMapping, Flavor
from app.models.k8s import PodCreation
from app.models.user import User
from app.db.session import SessionLocal

def create_test_mapping():
    """Generate test mappings based on user-provided data."""
    db = SessionLocal()
    try:
        # Check existing data
        servers = db.query(PodCreation).all()
        flavors = db.query(Flavor).all()
        users = db.query(User).all()
        
        print(f"Server count: {len(servers)}")
        print(f"GPU Flavor count: {len(flavors)}")
        print(f"User count: {len(users)}")
        
        # Delete existing mappings
        db.query(ServerGpuMapping).delete()
        print("Existing mapping data deleted")
        
        # Create mappings based on user data
        # server_id | gpu_id
        # ----------+--------
        #    12     | 120
        #    13     | 122
        #    14     | 118
        #    15     | 118
        #    15     | 119
        
        test_mappings = [
            (12, 120),  # server_id 12 -> gpu_id 120 
            (13, 122),  # server_id 13 -> gpu_id 122  
            (14, 118),  # server_id 14 -> gpu_id 118 
            (15, 118),  # server_id 15 -> gpu_id 118 
            (15, 119),  # server_id 15 -> gpu_id 119 
        ]
        
        created_count = 0
        for server_id, gpu_flavor_id in test_mappings:
            # Check if server and GPU actually exist
            server = db.query(PodCreation).filter(PodCreation.id == server_id).first()
            flavor = db.query(Flavor).filter(Flavor.id == gpu_flavor_id).first()
            
            if server and flavor:
                mapping = ServerGpuMapping(server_id=server_id, gpu_id=gpu_flavor_id)
                db.add(mapping)
                created_count += 1
                print(f"Mapping created: server_id={server_id} ({server.pod_name}) -> gpu_id={gpu_flavor_id} ({flavor.gpu_name})")
            else:
                print(f"Mapping failed: server_id={server_id} or gpu_id={gpu_flavor_id} does not exist")
                if not server:
                    print(f"  - Server {server_id} not found")
                if not flavor:
                    print(f"  - GPU Flavor {gpu_flavor_id} not found")
        
        db.commit()
        print(f"\nTotal {created_count} mappings created.")
        
        # Verify results
        mappings = db.query(ServerGpuMapping).all()
        print(f"\n=== Final Mapping Results ({len(mappings)} items) ===")
        for mapping in mappings:
            server = db.query(PodCreation).filter(PodCreation.id == mapping.server_id).first()
            flavor = db.query(Flavor).filter(Flavor.id == mapping.gpu_id).first()
            user = db.query(User).filter(User.id == server.user_id).first() if server else None
            
            if server and flavor:
                user_name = user.name if user else 'Unknown'
                print(f"server_id: {mapping.server_id} ({server.pod_name}) -> gpu_id: {mapping.gpu_id} ({flavor.gpu_name}) - User: {user_name}")
            
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_mapping() 