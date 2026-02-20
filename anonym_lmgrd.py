#!/usr/bin/env python3
"""
Anonymisiert lmgrd.log: user@machine -> user_XX@machine_YY
IGNORIERT: (@lmgrd-SLOG@) und Klammern direkt vor/nach @
Verwendung: python anonym_lmgrd.py lmgrd.log
"""

import sys
import os

def anonymize_lmgrd(input_file, output_file):
    """Anonymisiert User@Machine (ohne Klammern direkt vor/nach @)"""
    
    user_map = {}
    machine_map = {}
    user_counter = 1
    machine_counter = 1
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f_in:
            lines = f_in.readlines()
    except FileNotFoundError:
        print(f"FEHLER: {input_file} nicht gefunden!")
        return False
    
    print(f"Verarbeite {len(lines)} Zeilen...")
    
    for i, line in enumerate(lines):
        if '@' not in line:
            continue
            
        splitted = line.split()
        for j, part in enumerate(splitted):
            if '@' in part:
                user_machine = part.strip('"\' ')
                
                # IGNORIERE: (@lmgrd-SLOG@) Pattern
                if user_machine == '(@lmgrd-SLOG@)':
                    continue
                
                # IGNORIERE: Klammer direkt vor UND nach @ (z.B. (user)@(machine))
                if user_machine.startswith('(') and user_machine.endswith(')'):
                    paren_content = user_machine[1:-1]
                    if '@' in paren_content and paren_content.startswith('(') and paren_content.endswith(')'):
                        continue
                
                if '@' in user_machine:
                    try:
                        user_part, machine_part = user_machine.split('@', 1)
                        user_part = user_part.strip('()[]\'" ')
                        machine_part = machine_part.strip('()[]\'" ')
                        
                        # Überspringe wenn Klammer direkt vor/nach @ stand
                        if not user_part or not machine_part:
                            continue
                        
                        # Mapping erstellen
                        if user_part not in user_map:
                            user_map[user_part] = f"user_{user_counter:02d}"
                            user_counter += 1
                        
                        if machine_part not in machine_map:
                            machine_map[machine_part] = f"machine_{machine_counter:02d}"
                            machine_counter += 1
                        
                        # Ersetzen
                        new_part = f"{user_map[user_part]}@{machine_map[machine_part]}"
                        splitted[j] = new_part
                        lines[i] = ' '.join(splitted) + '\n'
                        break
                    except ValueError:
                        continue
                break
    
    # Speichern
    try:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.writelines(lines)
        print(f"✓ Erfolgreich: {output_file}")
        print(f"  {len(user_map)} User, {len(machine_map)} Maschinen")
        print(f"  User-Beispiele: {list(user_map.values())[:3]}")
        print(f"  Machine-Beispiele: {list(machine_map.values())[:3]}")
        return True
    except Exception as e:
        print(f"FEHLER beim Speichern: {e}")
        return False

def main():
    """Main Funktion mit sys.argv[1]"""
    if len(sys.argv) != 2:
        print("VERWENDUNG: python anonym_lmgrd.py lmgrd.log")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = input_file.replace('.log', '_anonym.log')
    
    if not os.path.exists(input_file):
        print(f"FEHLER: {input_file} nicht gefunden!")
        sys.exit(1)
    
    print(f"Lmgrd Anonymizer v1.2 - Klammer-Filter")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print("-" * 40)
    
    success = anonymize_lmgrd(input_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
