# app/db.py

from sqlalchemy import (
    create_engine, Column, Integer, String, ForeignKey,
    Float, Boolean, DateTime, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# === Configuración de la base de datos PostgreSQL ===
DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost:5432/dashboards_academicos"

# Crear motor de conexión y sesión
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Base declarativa para los modelos
Base = declarative_base()

# === MODELOS ===

class Usuario(Base):
    __tablename__ = 'usuarios'
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, nullable=False)
    contraseña_hash = Column(String(200), nullable=False)

    dashboards = relationship("Dashboard", back_populates="usuario")


class Materia(Base):
    __tablename__ = 'materias'
    id_materia = Column(Integer, primary_key=True)
    nombre_materia = Column(String(150), nullable=False)

    dashboards = relationship("Dashboard", back_populates="materia")


class Dashboard(Base):
    __tablename__ = 'dashboards'
    id_dashboard = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'))
    id_materia = Column(Integer, ForeignKey('materias.id_materia'))
    titulo_personalizado = Column(String(200))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    incluye_ets = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="dashboards")
    materia = relationship("Materia", back_populates="dashboards")
    evaluaciones = relationship("Evaluacion", back_populates="dashboard", cascade="all, delete")


class Evaluacion(Base):
    __tablename__ = 'evaluaciones'
    id_evaluacion = Column(Integer, primary_key=True)
    id_dashboard = Column(Integer, ForeignKey('dashboards.id_dashboard'))
    tipo_evaluacion = Column(String(20), nullable=False)  # ordinario, extraordinario, ets
    licenciatura = Column(String(150), nullable=False)
    grupo = Column(String(10), nullable=True)
    promedio_general = Column(Float)
    total_aprobados = Column(Integer)
    total_reprobados = Column(Integer)
    total_np = Column(Integer)

    dashboard = relationship("Dashboard", back_populates="evaluaciones")
    resultados = relationship("Resultado", back_populates="evaluacion", cascade="all, delete")


class Alumno(Base):
    __tablename__ = 'alumnos'
    id_alumno = Column(Integer, primary_key=True)
    boleta = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(150), nullable=False)
    genero = Column(String(15), CheckConstraint("genero IN ('Hombre', 'Mujer', 'Desconocido')"), nullable=False)

    resultados = relationship("Resultado", back_populates="alumno", cascade="all, delete")


class Resultado(Base):
    __tablename__ = 'resultados'
    id_resultado = Column(Integer, primary_key=True)
    id_evaluacion = Column(Integer, ForeignKey('evaluaciones.id_evaluacion'))
    id_alumno = Column(Integer, ForeignKey('alumnos.id_alumno'))
    calificacion = Column(Float)
    estatus = Column(String(20), CheckConstraint("estatus IN ('Aprobado', 'Reprobado', 'NP')"), nullable=False)

    evaluacion = relationship("Evaluacion", back_populates="resultados")
    alumno = relationship("Alumno", back_populates="resultados")


# === Crear todas las tablas (se llama desde app.py una vez) ===
def init_db():
    Base.metadata.create_all(bind=engine)
