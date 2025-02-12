using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using MedicalSystem.Data;
using MedicalSystem.Models;

namespace MedicalSystem.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class CheckupsController : ControllerBase
    {
        private readonly MedicalContext _context;

        public CheckupsController(MedicalContext context)
        {
            _context = context;
        }

        // GET: api/Checkups
        [HttpGet]
        public async Task<ActionResult<IEnumerable<Checkup>>> GetCheckups()
        {
            return await _context.Checkups.ToListAsync();
        }

        // GET: api/Checkups/5
        [HttpGet("{id}")]
        public async Task<ActionResult<Checkup>> GetCheckup(int id)
        {
            var checkup = await _context.Checkups.FindAsync(id);

            if (checkup == null)
            {
                return NotFound();
            }

            return checkup;
        }

        // PUT: api/Checkups/5
        // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        [HttpPut("{id}")]
        public async Task<IActionResult> PutCheckup(int id, Checkup checkup)
        {
            if (id != checkup.CheckupID)
            {
                return BadRequest();
            }

            _context.Entry(checkup).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!CheckupExists(id))
                {
                    return NotFound();
                }
                else
                {
                    throw;
                }
            }

            return NoContent();
        }

        // POST: api/Checkups
        // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        [HttpPost]
        public async Task<ActionResult<Checkup>> PostCheckup(Checkup checkup)
        {
            _context.Checkups.Add(checkup);
            await _context.SaveChangesAsync();

            return CreatedAtAction("GetCheckup", new { id = checkup.CheckupID }, checkup);
        }

        // DELETE: api/Checkups/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteCheckup(int id)
        {
            var checkup = await _context.Checkups.FindAsync(id);
            if (checkup == null)
            {
                return NotFound();
            }

            _context.Checkups.Remove(checkup);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool CheckupExists(int id)
        {
            return _context.Checkups.Any(e => e.CheckupID == id);
        }
    }
}
