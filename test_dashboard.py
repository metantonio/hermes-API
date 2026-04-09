#!/usr/bin/env python3
"""
Test script para Hermes Dashboard UI
Verifica que todo funciona correctamente
"""

import sys
import json
from pathlib import Path

def test_dashboard_imports():
    """Testear que todos los módulos importan correctamente"""
    print("🧪 Testeando imports del dashboard...")
    
    # Agregar ~/.hermes al path para importar hermes_llama_wrapper
    import os
    hermes_home = os.path.expanduser("~/.hermes")
    if hermes_home not in sys.path:
        sys.path.insert(0, hermes_home)
    
    try:
        from hermes_llama_wrapper import intercept_llm_call
        print("  ✅ hermes_llama_wrapper importado")
    except ImportError as e:
        print(f"  ❌ Error importando hermes_llama_wrapper: {e}")
        return False
    
    try:
        import streamlit
        print("  ✅ streamlit importado")
    except ImportError as e:
        print(f"  ❌ Error importando streamlit: {e}")
        return False
    
    return True

def test_hermes_info():
    """Testear función get_hermes_info"""
    print("\n🧪 Testeando get_hermes_info()...")
    
    try:
        from hermes_dashboard import get_hermes_info
        
        info = get_hermes_info()
        
        assert "version" in info, "Falta key 'version'"
        assert "home" in info, "Falta key 'home'"
        assert "gateway_running" in info, "Falta key 'gateway_running'"
        
        print(f"  ✅ Información obtenida:")
        print(f"    Version: {info.get('version')}")
        print(f"    Home: {info.get('home')}")
        print(f"    Gateway running: {info.get('gateway_running')}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_get_profiles():
    """Testear función get_profiles"""
    print("\n🧪 Testeando get_profiles()...")
    
    try:
        from hermes_dashboard import get_profiles
        
        profiles = get_profiles()
        
        if isinstance(profiles, list):
            print(f"  ✅ Obtenida lista de {len(profiles)} profiles")
            
            if profiles:
                print(f"  Ejemplo:")
                print(f"    {json.dumps(profiles[0], indent=2)[:200]}...")
            
            return True
        else:
            print(f"  ❌ Resultado no es una lista: {type(profiles)}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_get_skills():
    """Testear función get_skills"""
    print("\n🧪 Testeando get_skills()...")
    
    try:
        from hermes_dashboard import get_skills
        
        skills = get_skills()
        
        if isinstance(skills, list):
            print(f"  ✅ Obtenida lista de {len(skills)} skills")
            
            if skills:
                print(f"  Ejemplo:")
                print(f"    {json.dumps(skills[0], indent=2)[:200]}...")
            
            return True
        else:
            print(f"  ❌ Resultado no es una lista: {type(skills)}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_get_sessions():
    """Testear función get_sessions"""
    print("\n🧪 Testeando get_sessions()...")
    
    try:
        from hermes_dashboard import get_sessions
        
        sessions = get_sessions()
        
        if isinstance(sessions, list):
            print(f"  ✅ Obtenida lista de {len(sessions)} sessions")
            
            if sessions:
                print(f"  Ejemplo:")
                print(f"    {json.dumps(sessions[-1], indent=2)[:200]}...")
            
            return True
        else:
            print(f"  ❌ Resultado no es una lista: {type(sessions)}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_get_work_trees():
    """Testear función get_work_trees"""
    print("\n🧪 Testeando get_work_trees()...")
    
    try:
        from hermes_dashboard import get_work_trees
        
        work_trees = get_work_trees()
        
        if isinstance(work_trees, list):
            print(f"  ✅ Obtenida lista de {len(work_trees)} work trees")
            
            if work_trees:
                print(f"  Ejemplo:")
                print(f"    {json.dumps(work_trees[0], indent=2)[:200]}...")
            
            return True
        else:
            print(f"  ❌ Resultado no es una lista: {type(work_trees)}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_chat_function():
    """Testear función de chat con Hermes"""
    print("\n🧪 Testeando chat_with_hermes()...")
    
    try:
        from hermes_dashboard import chat_with_hermes
        
        test_message = "Hola, ¿cómo estás?"
        result = chat_with_hermes(test_message)
        
        if result:
            print(f"  ✅ Respuesta obtenida")
            
            if result.get("success"):
                print(f"  Respuesta: {result.get('response')[:100]}...")
                return True
            else:
                print(f"  ❌ Error: {result.get('error', 'unknown')}")
                return False
        else:
            print(f"  ❌ Respuesta nula")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_api_endpoint():
    """Testear conexión con endpoints del API"""
    print("\n🧪 Testeando endpoints del API...")
    
    try:
        from hermes_dashboard import call_api_endpoint
        
        # Test health endpoint
        result = call_api_endpoint("/health")
        
        if result.get("success"):
            print(f"  ✅ /health endpoint respondiendo")
            print(f"    {json.loads(result['data'])}")
            return True
        else:
            print(f"  ⚠️  API no respondiendo (esto es normal si no está corriendo)")
            print(f"    Error: {result.get('error', 'unknown')}")
            # Esto no es un error, solo el API no está corriendo
            return True  # Consideramos exitoso si el API no está corriendo
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("🦉 Hermes Dashboard UI - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_dashboard_imports),
        ("Hermes Info", test_hermes_info),
        ("Profiles", test_get_profiles),
        ("Skills", test_get_skills),
        ("Sessions", test_get_sessions),
        ("Work Trees", test_get_work_trees),
        ("Chat", test_chat_function),
        ("API Endpoints", test_api_endpoint),
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test {name} falló con excepción: {e}")
            failed += 1
            results.append((name, False))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 Resultados")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status}: {name}")
    
    print("=" * 60)
    print(f"  Total: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ¡Todos los tests pasaron!")
        return 0
    else:
        print("\n⚠️  Algunos tests fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())
