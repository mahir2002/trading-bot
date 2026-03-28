#!/usr/bin/env python3
"""
Binary Compilation Preparation Script
Identifies and extracts sensitive algorithms for IP protection
"""

import os
import ast
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AlgorithmAnalysis:
    """Analysis of algorithm sensitivity for IP protection."""
    file_path: str
    lines_of_code: int
    complexity_score: float
    ip_value: str  # LOW, MEDIUM, HIGH, CRITICAL
    business_impact: str
    compilation_priority: int  # 1 = highest priority
    contains_ml_models: bool
    contains_proprietary_logic: bool
    dependencies: List[str]

class IPProtectionAnalyzer:
    """Analyze codebase for IP protection priorities."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.sensitive_files: Dict[str, AlgorithmAnalysis] = {}
        self.keywords_high_value = {
            'lstm', 'transformer', 'ensemble', 'proprietary', 'advanced',
            'neural_network', 'deep_learning', 'machine_learning', 'ai_model',
            'prediction', 'forecasting', 'optimization', 'algorithm', 'strategy'
        }
        self.keywords_ml_models = {
            'fit', 'predict', 'train', 'model', 'classifier', 'regressor',
            'tensorflow', 'pytorch', 'sklearn', 'keras', 'xgboost'
        }
        
    def analyze_codebase(self) -> Dict[str, AlgorithmAnalysis]:
        """Analyze entire codebase for IP protection priorities."""
        print("🔍 Analyzing codebase for IP protection priorities...")
        
        # High-priority files based on your memories
        priority_files = [
            "advanced_ai_models_framework.py",
            "comprehensive_portfolio_risk_system.py", 
            "advanced_signal_generation_system.py",
            "comprehensive_backtesting_optimization_system.py",
            "dynamic_model_retraining_system.py",
            "advanced_time_series_forecasting.py",
            "multi_class_trading_classifier.py",
            "time_series_forecasting_integration.py"
        ]
        
        # Analyze all Python files
        for py_file in self.project_root.rglob("*.py"):
            if self._should_analyze_file(py_file):
                analysis = self._analyze_file(py_file)
                if analysis:
                    self.sensitive_files[str(py_file)] = analysis
        
        # Set priorities for known high-value files
        for file_path, analysis in self.sensitive_files.items():
            filename = Path(file_path).name
            if filename in priority_files:
                analysis.compilation_priority = 1
                analysis.ip_value = "CRITICAL"
        
        return self.sensitive_files
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if file should be analyzed."""
        # Skip test files, demos, and documentation
        skip_patterns = [
            'test_', '_test', 'demo_', '_demo', 'example_', '_example',
            '__pycache__', '.git', 'venv', 'env', 'node_modules'
        ]
        
        path_str = str(file_path).lower()
        return not any(pattern in path_str for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path) -> AlgorithmAnalysis:
        """Analyze individual file for IP sensitivity."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines_of_code = len([line for line in content.split('\n') 
                               if line.strip() and not line.strip().startswith('#')])
            
            # Calculate complexity and sensitivity scores
            complexity_score = self._calculate_complexity(content)
            contains_ml_models = self._contains_ml_models(content)
            contains_proprietary = self._contains_proprietary_logic(content)
            ip_value = self._assess_ip_value(content, lines_of_code, contains_ml_models)
            
            # Determine business impact
            business_impact = self._assess_business_impact(file_path.name, content)
            
            # Set compilation priority
            priority = self._determine_compilation_priority(
                ip_value, lines_of_code, contains_ml_models, contains_proprietary
            )
            
            # Extract dependencies
            dependencies = self._extract_dependencies(content)
            
            return AlgorithmAnalysis(
                file_path=str(file_path),
                lines_of_code=lines_of_code,
                complexity_score=complexity_score,
                ip_value=ip_value,
                business_impact=business_impact,
                compilation_priority=priority,
                contains_ml_models=contains_ml_models,
                contains_proprietary_logic=contains_proprietary,
                dependencies=dependencies
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate algorithmic complexity score."""
        try:
            tree = ast.parse(content)
            
            complexity_indicators = {
                'classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                'loops': len([n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))]),
                'conditions': len([n for n in ast.walk(tree) if isinstance(n, ast.If)]),
                'comprehensions': len([n for n in ast.walk(tree) if isinstance(n, (ast.ListComp, ast.DictComp))])
            }
            
            # Weighted complexity score
            complexity = (
                complexity_indicators['classes'] * 2 +
                complexity_indicators['functions'] * 1.5 +
                complexity_indicators['loops'] * 1 +
                complexity_indicators['conditions'] * 0.5 +
                complexity_indicators['comprehensions'] * 0.5
            )
            
            return min(complexity / 10, 10.0)  # Normalize to 0-10 scale
            
        except:
            return 0.0
    
    def _contains_ml_models(self, content: str) -> bool:
        """Check if file contains machine learning models."""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.keywords_ml_models)
    
    def _contains_proprietary_logic(self, content: str) -> bool:
        """Check if file contains proprietary algorithms."""
        content_lower = content.lower()
        
        # Look for proprietary indicators
        proprietary_indicators = [
            'proprietary', 'advanced', 'ensemble', 'lstm', 'transformer',
            'sophisticated', 'multi-class', 'confidence', 'optimization',
            'bayesian', 'genetic', 'walk-forward', 'regime', 'volatility'
        ]
        
        return any(indicator in content_lower for indicator in proprietary_indicators)
    
    def _assess_ip_value(self, content: str, lines_of_code: int, has_ml: bool) -> str:
        """Assess intellectual property value."""
        content_lower = content.lower()
        
        # Critical IP indicators
        if any(keyword in content_lower for keyword in ['lstm', 'transformer', 'ensemble']):
            return "CRITICAL"
        
        # High value indicators  
        if (lines_of_code > 500 and has_ml) or any(keyword in content_lower for keyword in 
            ['advanced', 'proprietary', 'optimization', 'sophisticated']):
            return "HIGH"
        
        # Medium value indicators
        if lines_of_code > 200 or has_ml:
            return "MEDIUM"
        
        return "LOW"
    
    def _assess_business_impact(self, filename: str, content: str) -> str:
        """Assess business impact of algorithm."""
        high_impact_files = [
            'advanced_ai_models', 'portfolio_risk', 'signal_generation',
            'backtesting', 'optimization', 'forecasting'
        ]
        
        if any(pattern in filename.lower() for pattern in high_impact_files):
            return "HIGH - Core trading algorithms"
        
        if 'trading' in filename.lower() or 'bot' in filename.lower():
            return "MEDIUM - Trading functionality"
        
        return "LOW - Supporting functionality"
    
    def _determine_compilation_priority(self, ip_value: str, lines: int, 
                                      has_ml: bool, has_proprietary: bool) -> int:
        """Determine compilation priority (1 = highest)."""
        if ip_value == "CRITICAL":
            return 1
        elif ip_value == "HIGH" and (lines > 500 or has_ml):
            return 2
        elif ip_value == "HIGH" or (has_proprietary and lines > 200):
            return 3
        elif ip_value == "MEDIUM" and lines > 100:
            return 4
        else:
            return 5
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract file dependencies."""
        dependencies = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)
        except:
            pass
        
        return list(set(dependencies))
    
    def generate_compilation_plan(self) -> Dict:
        """Generate binary compilation plan."""
        plan = {
            "compilation_priorities": {},
            "total_files": len(self.sensitive_files),
            "critical_files": 0,
            "high_value_files": 0,
            "estimated_effort": "TBD",
            "recommended_approach": "Hybrid Python/C++",
            "files_by_priority": {1: [], 2: [], 3: [], 4: [], 5: []}
        }
        
        for file_path, analysis in self.sensitive_files.items():
            priority = analysis.compilation_priority
            plan["files_by_priority"][priority].append({
                "file": Path(file_path).name,
                "full_path": file_path,
                "ip_value": analysis.ip_value,
                "lines_of_code": analysis.lines_of_code,
                "business_impact": analysis.business_impact,
                "contains_ml": analysis.contains_ml_models,
                "complexity": analysis.complexity_score
            })
            
            if analysis.ip_value == "CRITICAL":
                plan["critical_files"] += 1
            elif analysis.ip_value == "HIGH":
                plan["high_value_files"] += 1
        
        return plan
    
    def save_analysis_report(self, output_path: str = "ip_protection_analysis.json"):
        """Save analysis report to file."""
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_files_analyzed": len(self.sensitive_files),
            "compilation_plan": self.generate_compilation_plan(),
            "detailed_analysis": {
                file_path: {
                    "ip_value": analysis.ip_value,
                    "lines_of_code": analysis.lines_of_code,
                    "complexity_score": analysis.complexity_score,
                    "business_impact": analysis.business_impact,
                    "compilation_priority": analysis.compilation_priority,
                    "contains_ml_models": analysis.contains_ml_models,
                    "contains_proprietary_logic": analysis.contains_proprietary_logic,
                    "dependencies": analysis.dependencies
                }
                for file_path, analysis in self.sensitive_files.items()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Analysis report saved to {output_path}")
        return report

def create_binary_extraction_plan():
    """Create plan for extracting sensitive algorithms for compilation."""
    
    print("🛡️ IP Protection Analysis Starting...")
    print("=" * 60)
    
    # Analyze codebase
    analyzer = IPProtectionAnalyzer()
    sensitive_files = analyzer.analyze_codebase()
    
    # Generate compilation plan
    plan = analyzer.generate_compilation_plan()
    
    # Display results
    print(f"\n📊 Analysis Results:")
    print(f"   Total files analyzed: {plan['total_files']}")
    print(f"   Critical IP files: {plan['critical_files']}")
    print(f"   High-value files: {plan['high_value_files']}")
    
    print(f"\n🎯 Compilation Priorities:")
    for priority in [1, 2, 3]:
        files = plan["files_by_priority"][priority]
        if files:
            print(f"\n   Priority {priority} - {len(files)} files:")
            for file_info in files:
                print(f"     • {file_info['file']} ({file_info['lines_of_code']} lines)")
                print(f"       IP Value: {file_info['ip_value']}")
                print(f"       Impact: {file_info['business_impact']}")
    
    # Save detailed report
    report = analyzer.save_analysis_report()
    
    print(f"\n✅ IP Protection Analysis Complete!")
    print(f"   Report saved to: ip_protection_analysis.json")
    
    return report

if __name__ == "__main__":
    create_binary_extraction_plan() 