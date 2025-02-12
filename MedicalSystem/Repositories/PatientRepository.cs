using MedicalSystem.Data;
using MedicalSystem.Models;
using Microsoft.EntityFrameworkCore;

namespace MedicalSystem.Repositories
{
    public class PatientRepository : IRepository<Patient>
    {
        private readonly MedicalContext _context;

        public PatientRepository(MedicalContext context)
        {
            _context = context;
        }

        public async Task<IEnumerable<Patient>> GetAllAsync()
        {
            return await _context.Patients.Include(p => p.MedicalRecords)
                                          .Include(p => p.Checkups)
                                          .ToListAsync();
        }

        public async Task<Patient> GetByIdAsync(int id)
        {
            return await _context.Patients.Include(p => p.MedicalRecords)
                                          .Include(p => p.Checkups)
                                          .FirstOrDefaultAsync(p => p.Id == id);
        }

        public async Task AddAsync(Patient patient)
        {
            await _context.Patients.AddAsync(patient);
        }

        public async Task UpdateAsync(Patient patient)
        {
            _context.Patients.Update(patient);
        }

        public async Task DeleteAsync(int id)
        {
            var patient = await _context.Patients.FindAsync(id);
            if (patient != null)
            {
                _context.Patients.Remove(patient);
            }
        }

        public async Task SaveAsync()
        {
            await _context.SaveChangesAsync();
        }
    }
}