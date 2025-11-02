"""PDF parsing service for extracting and structuring data from PDF files."""

import logging
import re
from typing import Dict, List, Optional

import pdfplumber
from pypdf import PdfReader

from src.infrastructure.ai import GeminiClient

logger = logging.getLogger(__name__)


class PDFParserService:
    """Service for parsing PDF files and extracting structured data."""

    def __init__(self, gemini_client: GeminiClient):
        """Initialize PDF parser service.
        
        Args:
            gemini_client: Gemini AI client for text structuring
        """
        self.gemini_client = gemini_client

    async def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF file.
        
        Args:
            pdf_content: PDF file content in bytes
            
        Returns:
            Extracted text
            
        Raises:
            ValueError: If PDF is invalid or empty
        """
        try:
            import io
            
            text_parts = []
            
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            text = "\n\n".join(text_parts)
            
            if not text.strip():
                pdf_reader = PdfReader(io.BytesIO(pdf_content))
                text_parts = []
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                text = "\n\n".join(text_parts)
            
            if not text.strip():
                raise ValueError("Не удалось извлечь текст из PDF")
            
            logger.info(f"Извлечено {len(text)} символов текста из PDF")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из PDF: {e}")
            raise ValueError(f"Ошибка при чтении PDF файла: {str(e)}")

    async def structure_vacancy_from_text(self, text: str) -> Dict:
        """Structure vacancy data from extracted text using AI.
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            Structured vacancy data
        """
        prompt = f"""
Проанализируй следующий текст вакансии и извлеки из него структурированную информацию.
Верни ответ СТРОГО в формате JSON без дополнительных пояснений.

Текст вакансии:
{text}

Верни JSON в таком формате:
{{
    "title": "название вакансии",
    "description": "детальное описание вакансии",
    "requirements": ["требование 1", "требование 2", ...],
    "responsibilities": ["обязанность 1", "обязанность 2", ...],
    "skills": ["навык 1", "навык 2", ...],
    "experience_years": число_лет_опыта_или_null,
    "salary_range": "диапазон_зарплаты_или_null",
    "location": "местоположение_или_null",
    "employment_type": "тип_занятости (full-time/part-time/contract/remote)"
}}

Если какое-то поле не найдено, используй разумные значения по умолчанию.
Для списков верни хотя бы несколько элементов, извлеченных из текста.
"""
        
        try:
            response = await self.gemini_client.generate_response(prompt)
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                data = json.loads(json_match.group())
                
                required_fields = ["title", "description"]
                for field in required_fields:
                    if not data.get(field):
                        raise ValueError(f"Обязательное поле '{field}' не найдено или пустое")
                
                list_fields = ["requirements", "responsibilities", "skills"]
                for field in list_fields:
                    if field not in data or not isinstance(data[field], list):
                        data[field] = []
                
                if "employment_type" not in data or not data["employment_type"]:
                    data["employment_type"] = "full-time"
                
                logger.info(f"Структурированы данные вакансии: {data.get('title')}")
                return data
            else:
                logger.error(f"AI ответ не содержит JSON. Ответ: {response[:500]}")
                raise ValueError("AI не вернул валидный JSON")
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}. Ответ AI: {response[:500]}")
            raise ValueError(f"Не удалось распарсить ответ AI: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка при структурировании данных вакансии: {e}")
            raise ValueError(f"Не удалось структурировать данные: {str(e)}")

    async def structure_candidate_from_text(self, text: str) -> Dict:
        """Structure candidate data from extracted text using AI.
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            Structured candidate data
        """
        prompt = f"""
Проанализируй следующее резюме кандидата и извлеки из него структурированную информацию.
Верни ответ СТРОГО в формате JSON без дополнительных пояснений.

Текст резюме:
{text}

Верни JSON в таком формате:
{{
    "name": "ФИО кандидата",
    "email": "email@example.com",
    "phone": "телефон_или_null",
    "summary": "краткое резюме/описание кандидата",
    "skills": ["навык 1", "навык 2", ...],
    "experience": ["опыт работы 1", "опыт работы 2", ...],
    "education": ["образование 1", "образование 2", ...],
    "experience_years": число_лет_опыта_или_null,
    "desired_position": "желаемая_должность_или_null",
    "desired_salary": "желаемая_зарплата_или_null",
    "location": "местоположение_или_null"
}}

Если какое-то поле не найдено, используй разумные значения по умолчанию.
Для списков верни хотя бы несколько элементов, извлеченных из текста.
Email ОБЯЗАТЕЛЬНО должен быть в правильном формате или сгенерируй placeholder вида "candidate@example.com".
"""
        
        try:
            response = await self.gemini_client.generate_response(prompt)
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                data = json.loads(json_match.group())
                
                if not data.get("name"):
                    raise ValueError(f"Обязательное поле 'name' не найдено или пустое")
                
                if not data.get("email"):
                    data["email"] = "candidate@example.com"
                
                if not data.get("summary"):
                    summary_parts = []
                    if data.get("experience_years"):
                        summary_parts.append(f"Профессионал с {data['experience_years']} годами опыта")
                    if data.get("skills"):
                        skills_text = ", ".join(data["skills"][:3])
                        summary_parts.append(f"Владеет навыками: {skills_text}")
                    if data.get("desired_position"):
                        summary_parts.append(f"Ищет позицию: {data['desired_position']}")
                    
                    data["summary"] = ". ".join(summary_parts) if summary_parts else "Опытный специалист"
                
                if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", data["email"]):
                    data["email"] = "candidate@example.com"
                
                list_fields = ["skills", "experience", "education"]
                for field in list_fields:
                    if field not in data or not isinstance(data[field], list):
                        data[field] = []
                
                logger.info(f"Структурированы данные кандидата: {data.get('name')}")
                return data
            else:
                logger.error(f"AI ответ не содержит JSON. Ответ: {response[:500]}")
                raise ValueError("AI не вернул валидный JSON")
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}. Ответ AI: {response[:500]}")
            raise ValueError(f"Не удалось распарсить ответ AI: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка при структурировании данных кандидата: {e}")
            raise ValueError(f"Не удалось структурировать данные: {str(e)}")

    async def parse_vacancy_pdf(self, pdf_content: bytes) -> Dict:
        """Parse vacancy PDF and return structured data.
        
        Args:
            pdf_content: PDF file content
            
        Returns:
            Structured vacancy data ready for VacancyCreate schema
        """
        text = await self.extract_text_from_pdf(pdf_content)
        structured_data = await self.structure_vacancy_from_text(text)
        return structured_data

    async def parse_candidate_pdf(self, pdf_content: bytes) -> Dict:
        """Parse candidate PDF and return structured data.
        
        Args:
            pdf_content: PDF file content
            
        Returns:
            Structured candidate data ready for CandidateCreate schema
        """
        text = await self.extract_text_from_pdf(pdf_content)
        structured_data = await self.structure_candidate_from_text(text)
        return structured_data

    async def parse_vacancies_batch(
        self, pdf_contents: List[bytes], filenames: List[str]
    ) -> List[Dict]:
        """
        Parse multiple vacancy PDFs at once using single AI call.
        
        Args:
            pdf_contents: List of PDF file contents
            filenames: List of filenames for logging
            
        Returns:
            List of structured vacancy data
        """
        logger.info(f"Batch parsing {len(pdf_contents)} vacancy PDFs...")
        
        # Извлекаем тексты из всех PDF
        extracted_texts = []
        for idx, (pdf_content, filename) in enumerate(zip(pdf_contents, filenames), 1):
            try:
                text = await self.extract_text_from_pdf(pdf_content)
                extracted_texts.append({
                    "index": idx,
                    "filename": filename,
                    "text": text
                })
                logger.info(f"Извлечен текст из PDF {idx}/{len(pdf_contents)}: {filename}")
            except Exception as e:
                logger.error(f"Ошибка при извлечении текста из {filename}: {e}")
                # Пропускаем этот файл
                continue
        
        if not extracted_texts:
            raise ValueError("Не удалось извлечь текст ни из одного PDF файла")
        
        # Формируем один большой промпт для всех вакансий
        prompt = f"""
Проанализируй следующие {len(extracted_texts)} вакансий из PDF файлов и извлеки из каждого структурированную информацию.
Верни ответ СТРОГО в формате JSON массива без дополнительных пояснений.

"""
        
        for item in extracted_texts:
            prompt += f"""
=== ВАКАНСИЯ {item['index']} (файл: {item['filename']}) ===
{item['text']}

"""
        
        prompt += """
Верни JSON массив в таком формате (ВАЖНО: это должен быть массив объектов):
[
    {
        "title": "название вакансии 1",
        "description": "детальное описание вакансии 1",
        "requirements": ["требование 1", "требование 2", ...],
        "responsibilities": ["обязанность 1", "обязанность 2", ...],
        "skills": ["навык 1", "навык 2", ...],
        "experience_years": число_лет_опыта_или_null,
        "salary_range": "диапазон_зарплаты_или_null",
        "location": "местоположение_или_null",
        "employment_type": "тип_занятости (full-time/part-time/contract/remote)"
    },
    {
        "title": "название вакансии 2",
        ...
    }
]

ВАЖНО: 
- Верни РОВНО столько объектов в массиве, сколько было вакансий
- Сохрани порядок вакансий как в исходных данных
- Для каждой вакансии обязательно заполни title и description
- Если какое-то поле не найдено, используй разумные значения по умолчанию
"""
        
        try:
            response = await self.gemini_client.generate_response(prompt)
            
            # Ищем JSON массив в ответе
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                import json
                vacancies_data = json.loads(json_match.group())
                
                if not isinstance(vacancies_data, list):
                    raise ValueError("AI не вернул массив")
                
                # Валидация каждой вакансии
                validated_vacancies = []
                for idx, data in enumerate(vacancies_data, 1):
                    required_fields = ["title", "description"]
                    for field in required_fields:
                        if not data.get(field):
                            raise ValueError(f"Вакансия {idx}: обязательное поле '{field}' не найдено")
                    
                    list_fields = ["requirements", "responsibilities", "skills"]
                    for field in list_fields:
                        if field not in data or not isinstance(data[field], list):
                            data[field] = []
                    
                    if "employment_type" not in data or not data["employment_type"]:
                        data["employment_type"] = "full-time"
                    
                    validated_vacancies.append(data)
                
                logger.info(f"Успешно структурировано {len(validated_vacancies)} вакансий")
                return validated_vacancies
            else:
                logger.error(f"AI ответ не содержит JSON массив. Ответ: {response[:1000]}")
                raise ValueError("AI не вернул валидный JSON массив")
                
        except Exception as e:
            logger.error(f"Ошибка при batch обработке вакансий: {e}")
            raise ValueError(f"Не удалось обработать вакансии: {str(e)}")

    async def parse_candidates_batch(
        self, pdf_contents: List[bytes], filenames: List[str]
    ) -> List[Dict]:
        """
        Parse multiple candidate PDFs at once using single AI call.
        
        Args:
            pdf_contents: List of PDF file contents
            filenames: List of filenames for logging
            
        Returns:
            List of structured candidate data
        """
        logger.info(f"Batch parsing {len(pdf_contents)} candidate PDFs...")
        
        # Извлекаем тексты из всех PDF
        extracted_texts = []
        for idx, (pdf_content, filename) in enumerate(zip(pdf_contents, filenames), 1):
            try:
                text = await self.extract_text_from_pdf(pdf_content)
                extracted_texts.append({
                    "index": idx,
                    "filename": filename,
                    "text": text
                })
                logger.info(f"Извлечен текст из PDF {idx}/{len(pdf_contents)}: {filename}")
            except Exception as e:
                logger.error(f"Ошибка при извлечении текста из {filename}: {e}")
                continue
        
        if not extracted_texts:
            raise ValueError("Не удалось извлечь текст ни из одного PDF файла")
        
        # Формируем один большой промпт для всех кандидатов
        prompt = f"""
Проанализируй следующие {len(extracted_texts)} резюме кандидатов из PDF файлов и извлеки из каждого структурированную информацию.
Верни ответ СТРОГО в формате JSON массива без дополнительных пояснений.

"""
        
        for item in extracted_texts:
            prompt += f"""
=== РЕЗЮМЕ {item['index']} (файл: {item['filename']}) ===
{item['text']}

"""
        
        prompt += """
Верни JSON массив в таком формате (ВАЖНО: это должен быть массив объектов):
[
    {
        "name": "ФИО кандидата 1",
        "email": "email1@example.com",
        "phone": "телефон_или_null",
        "summary": "краткое резюме/описание кандидата 1",
        "skills": ["навык 1", "навык 2", ...],
        "experience": ["опыт работы 1", "опыт работы 2", ...],
        "education": ["образование 1", "образование 2", ...],
        "experience_years": число_лет_опыта_или_null,
        "desired_position": "желаемая_должность_или_null",
        "desired_salary": "желаемая_зарплата_или_null",
        "location": "местоположение_или_null"
    },
    {
        "name": "ФИО кандидата 2",
        ...
    }
]

ВАЖНО:
- Верни РОВНО столько объектов в массиве, сколько было резюме
- Сохрани порядок резюме как в исходных данных
- Для каждого кандидата обязательно заполни name и email
- Email ОБЯЗАТЕЛЬНО должен быть в правильном формате или используй "resume{номер}@example.com"
- Если какое-то поле не найдено, используй разумные значения по умолчанию
"""
        
        try:
            response = await self.gemini_client.generate_response(prompt)
            
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                import json
                candidates_data = json.loads(json_match.group())
                
                if not isinstance(candidates_data, list):
                    raise ValueError("AI не вернул массив")
                
                # Валидация каждого кандидата
                validated_candidates = []
                for idx, data in enumerate(candidates_data, 1):
                    if not data.get("name"):
                        data["name"] = f"Кандидат {idx}"
                    
                    if not data.get("email") or not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", data.get("email", "")):
                        data["email"] = f"resume{idx}@example.com"
                    
                    if not data.get("summary"):
                        summary_parts = []
                        if data.get("experience_years"):
                            summary_parts.append(f"Профессионал с {data['experience_years']} годами опыта")
                        if data.get("skills"):
                            skills_text = ", ".join(data["skills"][:3])
                            summary_parts.append(f"Владеет навыками: {skills_text}")
                        if data.get("desired_position"):
                            summary_parts.append(f"Ищет позицию: {data['desired_position']}")
                        
                        data["summary"] = ". ".join(summary_parts) if summary_parts else f"Опытный специалист (резюме {idx})"
                    
                    list_fields = ["skills", "experience", "education"]
                    for field in list_fields:
                        if field not in data or not isinstance(data[field], list):
                            data[field] = []
                    
                    validated_candidates.append(data)
                
                logger.info(f"Успешно структурировано {len(validated_candidates)} кандидатов")
                return validated_candidates
            else:
                logger.error(f"AI ответ не содержит JSON массив. Ответ: {response[:1000]}")
                raise ValueError("AI не вернул валидный JSON массив")
                
        except Exception as e:
            logger.error(f"Ошибка при batch обработке кандидатов: {e}")
            raise ValueError(f"Не удалось обработать кандидатов: {str(e)}")

