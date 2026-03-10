import re
from typing import Dict, Optional, List
from datetime import datetime
import pdfplumber
import fitz
from pypdf import PdfReader

def extract_text_pdfplumber(pdf_path: str, debug: bool) -> str:
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except Exception as e:
        if debug:
            print(f"DEBUG (pdfplumber): Erro - {e}")
    return full_text

def extract_text_fitz(pdf_path: str, debug: bool) -> str:
    full_text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text = page.get_text("text")
                if text:
                    full_text += text + "\n"
    except Exception as e:
        if debug:
            print(f"DEBUG (fitz): Erro - {e}")
    return full_text

def extract_text_pypdf(pdf_path: str, debug: bool) -> str:
    full_text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    except Exception as e:
        if debug:
            print(f"DEBUG (pypdf): Erro - {e}")
    return full_text

def limpar_texto(texto: str) -> str:
    texto = re.sub(r'[\t\r]', ' ', texto)
    texto = re.sub(r' +', ' ', texto)
    return re.sub(r'\n+', '\n', texto).strip()

def extrair_cpf(text: str) -> Optional[str]:
    """
    Procura CPF em vários formatos e retorna formatado como xxx.xxx.xxx-xx
    """
    patterns = [
        r'CPF[:\s]*([\d]{3}\.[\d]{3}\.[\d]{3}-[\d]{2})',
        r'CPF[:\s]*([\d]{11})',
        r'CPF[:\s]*([\d]{3}\s[\d]{3}\s[\d]{3}\s[\d]{2})',
        r'([\d]{3}\.[\d]{3}\.[\d]{3}-[\d]{2})',  # sem label
        r'\b(\d{11})\b'  
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            raw = re.sub(r'\D', '', m.group(1))
            if len(raw) == 11:
                return f"{raw[0:3]}.{raw[3:6]}.{raw[6:9]}-{raw[9:11]}"
    return None

def extrair_medico_pcmso(text: str) -> Optional[str]:
    patterns = [
        r'MÉDICO\s+RESPONSÁVEL\s+PELO\s+PCMSO\s+([A-ZÀ-Úa-zà-ú\.\-\s]{5,100}?)(?=\s*(?:RISCOS|SETOR|CARGO|$))',
        r'MÉDICO\s+RESPONSÁVEL\s+PELO\s+PCMSO\n([A-ZÀ-Úa-zà-ú\.\-\s]{5,100})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            nome = limpar_texto(match.group(1))
            nome = re.sub(r'(?:Responsável pelo PCMSO|PCMSO)', '', nome, flags=re.IGNORECASE)
            nome = limpar_texto(nome)
            if len(nome.split()) >= 2 and len(nome) > 5:
                return nome.upper()
    return None

def extrair_medico_examinador(text: str, pdf_path: Optional[str] = None) -> Optional[str]:
    pattern_nome_crm = r'([A-ZÀ-ÚA-Za-zà-ú\s\.]{5,100})[-–—]\s*\d{4,6}\s*[\/\-]?\s*[A-Z]{2}'
    matches = re.findall(pattern_nome_crm, text)
    if matches:
        nomes = [limpar_texto(m).upper() for m in matches if len(m.split()) >= 2]
        if nomes:
            return nomes[-1]

    patterns_digital = [
        r'Assinado\s+(?:biometricamente|digitalmente)\s+por:\s*([A-ZÀ-ÚA-Za-zà-ú\s\.]+?)(?=[\:\,\n])',
        r'(?:Médico Examinador|MÉDICO EXAMINADOR)["\'\s:\-]*\n?\s*([A-ZÀ-ÚA-Za-zà-ú\.\-\s]{5,100}?)(?:\s*[-–—]?\s*(?:CRM\.?\s*)?\d{4,6})'
    ]
    for pattern in patterns_digital:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            nome = limpar_texto(match.group(1))
            nome = re.sub(r'[\*\d]+', '', nome)
            if len(nome.split()) >= 2 and len(nome) > 5:
                return nome.upper()

    if pdf_path:
        try:
            import fitz
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text_page = page.get_text("text")
                    matches = re.findall(pattern_nome_crm, text_page)
                    if matches:
                        nomes = [limpar_texto(m).upper() for m in matches if len(m.split()) >= 2]
                        if nomes:
                            return nomes[-1]
        except Exception as e:
            print(f"DEBUG (fitz): Falha ao abrir PDF: {e}")

    return None

def extrair_todos_medicos_com_crm(text: str) -> List[Dict[str, str]]:
    medicos = []
    patterns = [
        r'([A-ZÀ-Ú][A-ZÀ-Úa-zà-ú\.\s]{5,100}?)\s*[-–—]?\s*(?:CRM\.?\s*)?(\d{4,6})\s*[\/\-]?\s*([A-Z]{2})',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            nome = limpar_texto(match.group(1))
            nome = re.sub(r'\b(?:CRM|RGE|Medicina|do|Trabalho|Responsável|pelo|PCMSO|Dr|Dra)\b', '', nome, flags=re.IGNORECASE)
            nome = limpar_texto(nome)
            if len(nome.split()) >= 2 and len(nome) > 5:
                medicos.append({'nome': nome.upper(), 'posicao': match.start()})
    nomes_vistos = set()
    medicos_unicos = []
    for medico in sorted(medicos, key=lambda x: x['posicao']):
        if medico['nome'] not in nomes_vistos:
            medicos_unicos.append(medico)
            nomes_vistos.add(medico['nome'])
    return medicos_unicos

def extrair_cargo(text: str) -> Optional[str]:
    """
    Extrai o cargo com base nas regras:
    - Começa depois de 'Masculino' ou 'Feminino'
    - Termina antes de 'Setor'
    - Remove 'Cargo:' intermediário e une quebras de linha
    - Junta tudo em uma única linha
    """
    texto = limpar_texto(text)

    padrao = re.compile(
        r'(?:Masculino|Feminino)\s+([\s\S]+?)(?=\s*Setor\b|$)',
        re.IGNORECASE
    )
    m = padrao.search(texto)
    if not m:
        return None

    trecho = m.group(1)

    trecho = re.split(r'\bSetor\b', trecho, flags=re.IGNORECASE)[0]

    trecho = re.sub(r'\bCargo[:\s]*', ' ', trecho, flags=re.IGNORECASE)

    trecho = re.sub(r'\s+', ' ', trecho).strip()

    if 3 < len(trecho) < 300:
        return trecho.upper()

    return None



def extrair_funcionario(text: str) -> Optional[str]:
    patterns = [r'Nome[:\s]+\n?\s*([\s\S]+?)(?=\s+(?:Matrícula|CPF|Cargo|Setor|Nascimento|Idade|RG))', r'FUNCIONÁRIO[\s\S]*?Nome[:\s]+\n?\s*([A-ZÀ-Úa-zà-ú\s]+?)(?=\s+(?:Matrícula|CPF))', r'Nome[:\s]*\n([A-ZÀ-Úa-zà-ú\s]+?)(?=\n)']
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            n = limpar_texto(m.group(1))
            if len(n.split()) >= 2 and len(n) > 5:
                return n.upper()
    return None

def extrair_tipo_exame(text: str) -> Optional[str]:
    patterns = [r'TIPO\s+DE\s+EXAME[\s\n]*([A-ZÀ-Úa-zà-ú0-9\s]+?)(?=\s*(?:AVALIAÇÃO|RESULTADO|Apto|Inapto|$))', r'TIPO\s+DE\s+EXAME[\s:\n]*([^\n]+)']
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            t = limpar_texto(m.group(1))
            if len(t) > 3 and len(t) < 50:
                return t.title()
    return None

def extrair_resultado_exame(text: str) -> Optional[str]:
    patterns = [r'RESULTADO\s+DO\s+EXAME[\s\n]*(Apto|Inapto)[\s\w]*', r'(Apto|Inapto)\s+para\s+função']
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip().capitalize()
    return None

def extrair_data_exame(text: str) -> Optional[str]:
    patterns = [r'(\d{2}/\d{2}/\d{4})\s*Exame\s+Clínico', r'Exame\s+Clínico\s*(\d{2}/\d{2}/\d{4})', r'AVALIAÇÃO\s+CLÍNICA[\s\S]{0,100}?(\d{2}/\d{2}/\d{4})', r'Data:\s*(\d{2}/\d{2}/\d{4})']
    datas = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            try:
                datetime.strptime(m.group(1), '%d/%m/%Y')
                datas.append(m.group(1))
            except ValueError:
                continue
    return datas[0] if datas else None

def extrair_matricula(text: str) -> Optional[str]:
    """
    Extrai a matrícula a partir do padrão:
    'Matrícula eSocial: 778' (ou similar)
    Sempre vem depois do nome e antes do CPF.
    """
    texto = limpar_texto(text)
    match = re.search(r'Matr[íi]cula\s*eSocial[:\s]*([A-Za-z0-9\-\/]+)', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'Matr[íi]cula[:\s]*([A-Za-z0-9\-\/]+)', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_aso_info(text: str, debug: bool = False, source_name: str = "Digital", pdf_path: Optional[str] = None) -> Dict[str, Optional[str]]:
    results = {
        "Funcionario": None, "CPF": None, "Medico_PCMSO": None, "Medico_Examinador_ASO": None,
        "Tipo_Exame": None, "Resultado_Exame": None, "Data_Exame_Clinico": None, "Cargo": None,
        "Matricula": None
    }
    cleaned_text = limpar_texto(text)
    if not cleaned_text:
        return results
    results["Funcionario"] = extrair_funcionario(cleaned_text)
    results["CPF"] = extrair_cpf(cleaned_text)
    results["Cargo"] = extrair_cargo(cleaned_text)
    results["Tipo_Exame"] = extrair_tipo_exame(cleaned_text)
    results["Resultado_Exame"] = extrair_resultado_exame(cleaned_text)
    results["Data_Exame_Clinico"] = extrair_data_exame(cleaned_text)
    results["Medico_PCMSO"] = extrair_medico_pcmso(cleaned_text)
    results["Medico_Examinador_ASO"] = extrair_medico_examinador(cleaned_text, pdf_path)
    results["Matricula"] = extrair_matricula(cleaned_text)
    if debug:
        print(f"DEBUG ({source_name}) PCMSO: {results['Medico_PCMSO']}")
        print(f"DEBUG ({source_name}) Examinador: {results['Medico_Examinador_ASO']}")
        print(f"DEBUG ({source_name}) CPF: {results['CPF']}")
        print(f"DEBUG ({source_name}) Cargo: {results['Cargo']}")
    if results["Medico_PCMSO"] is None or results["Medico_Examinador_ASO"] is None:
        todos_medicos = extrair_todos_medicos_com_crm(cleaned_text)
        if todos_medicos:
            if results["Medico_PCMSO"] is None:
                results["Medico_PCMSO"] = todos_medicos[0]['nome']
            if results["Medico_Examinador_ASO"] is None:
                nome_examinador = next((m['nome'] for m in todos_medicos if m['nome'] != results["Medico_PCMSO"]), None)
                results["Medico_Examinador_ASO"] = nome_examinador if nome_examinador else results["Medico_PCMSO"]
    return results

def extrair_dados_pdf(pdf_path: str, debug: bool = False) -> Dict[str, Optional[str]]:
    if debug:
        print(f"\n=== INICIANDO EXTRAÇÃO ROBUSTA: {pdf_path} ===")
    results = {
        "Funcionario": None, "CPF": None, "Medico_PCMSO": None, "Medico_Examinador_ASO": None,
        "Tipo_Exame": None, "Resultado_Exame": None, "Data_Exame_Clinico": None, "Cargo": None,
        "Matricula": None
    }
    extractors = [
        ("pdfplumber", extract_text_pdfplumber),
        ("pypdf", extract_text_pypdf),
        ("fitz", extract_text_fitz),
    ]
    for source_name, extractor_func in extractors:
        if debug:
            print(f"\n--- TENTANDO: {source_name} ---")
        text = extractor_func(pdf_path, debug)
        if text.strip():
            current_results = extract_aso_info(text, debug, source_name, pdf_path)
            for key in results:
                if results[key] is None and current_results.get(key) is not None:
                    if debug:
                        print(f"DEBUG (Merge): {key} atualizado ({source_name}) -> {current_results.get(key)}")
                    results[key] = current_results.get(key)
            if results["Medico_Examinador_ASO"] and results["Medico_PCMSO"]:
                if debug:
                    print("\n>>> SUCESSO: Ambos médicos encontrados.")
                break
        else:
            if debug:
                print(f"ALERTA: {source_name} não extraiu texto.")
    if debug:
        print("\n=== RESULTADOS FINAIS ===")
        for k, v in results.items():
            print(f"{k}: {v}")
        print("=" * 50)
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        resultados = extrair_dados_pdf(pdf_path, debug=True)
    else:
        print("Uso: python extrair_dados_do_pdf.py <arquivo.pdf>")
