namespace MedicalSystem.Data
{
    using MedicalSystem.Models;
    using Microsoft.EntityFrameworkCore;

    public class MedicalContext : DbContext
    {
        public DbSet<Patient> Patients { get; set; }
        public DbSet<MedicalRecord> MedicalRecords { get; set; }
        public DbSet<Checkup> Checkups { get; set; }

        // Constructor to configure the database connection
        public MedicalContext(DbContextOptions<MedicalContext> options) : base(options) { }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            // Unique constraint on PatientID
            modelBuilder.Entity<Patient>()
                .HasIndex(p => p.PatientID)
                .IsUnique();

            // One-to-Many: Patient -> MedicalRecords
            modelBuilder.Entity<MedicalRecord>()
                .HasOne(m => m.Patient)
                .WithMany(p => p.MedicalRecords)
                .HasForeignKey(m => m.PatientId)
                .OnDelete(DeleteBehavior.Cascade);

            // One-to-Many: Patient -> Checkups
            modelBuilder.Entity<Checkup>()
                .HasOne(c => c.Patient)
                .WithMany(p => p.Checkups)
                .HasForeignKey(c => c.PatientId)
                .OnDelete(DeleteBehavior.Cascade);
        }
    }
}
