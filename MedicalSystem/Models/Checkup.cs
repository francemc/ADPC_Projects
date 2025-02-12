namespace MedicalSystem.Models
{
    public class Checkup
    {
        public int CheckupID { get; set; } // Primary Key
        public int PatientId { get; set; } // Foreign Key
        public DateTime CheckupDate { get; set; }
        public string ProcedureCode { get; set; }
        public string? ImageURL { get; set; } // MinIO Image Storage

        // Corrected Navigation Property for Lazy Loading
        public virtual Patient Patient { get; set; }
    }
}

